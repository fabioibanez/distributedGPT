from __future__ import annotations
from typing import List, Dict, Tuple
from PoolInterface import PoolInterface
from concurrent import futures
from Custodian import MultiAgentCustodian
from queue import Queue
from messages import AgentMessage

from utils.llmAPI import gpt4Llm
from utils.constants import *

from memgpt.models.chat_completion_response import ChatCompletionResponse

import json

import grpc
import distributed_gpt_pb2_grpc
import distributed_gpt_pb2
from threading import Lock, Condition

Status = dict
ProcessID = int


class LeaderServicer(distributed_gpt_pb2_grpc.LeaderServicer):
    
    @staticmethod
    def data_structures() -> Dict[str, str]:
        return {
            "job_id_to_response": "a map from a user submitted job to the response struct for that job",
        }
     
    
    def __init__(self, assoc_interface: PoolRPCInterface):
        super().__init__()
        self.assoc_interface = assoc_interface
        self.proc_id_counter = 0
        self.job_id_counter = 0
        self.job_id_to_response : Dict[int, distributed_gpt_pb2.JobResponse] = {}
        self.llm_connection = gpt4Llm()
        self.persona_dict: Dict[int, str] = dict()

    def submitJob(self, request: distributed_gpt_pb2.JobRequest, context):
        """
        Returns a ticket to the job requestor so that they can query the state of a job
        """
        
        log(f"(SERVER) Got a job from client with identity {context.peer()}!", Logging.INFO.value)
        
        system_msg = DOCUMENT_MAPPING_MESSAGE % json.dumps(self.persona_dict)
        
        document_dict = dict(request.files)
        prompt = json.dumps(document_dict)

        
        log(f"(SERVER) Sending the following document dictionary to GPT...", Logging.INFO.value)
        log(json.dumps(document_dict, indent=1), Logging.DATA.value)

        res : ChatCompletionResponse = self.llm_connection.make_request(persona=system_msg, prompt=prompt, model='gpt-4o')

        document_to_agent_mapping = res.content
        log(f"(SERVER) GPT sent me corresponding mapping:", Logging.INFO.value)
        log(document_to_agent_mapping, Logging.DATA.value)

        # add request to job queue
        self.assoc_interface.jobs_queue.put((self.job_id_counter, document_to_agent_mapping, request))
        self.assoc_interface.dispatch_job()
        
        self.job_id_counter += 1
        return distributed_gpt_pb2.JobResponse(status=JobStatus.PENDING.value, response=None)
        
    def getJob(self, request, context):
        """
        Returns an object with the status of a job and the result of the job
        """
        log(
            f"(SERVER) Got a job status request from client with identity {context.peer()}!", 
            Logging.INFO.value
        )

        if (request.ticket not in self.job_id_to_response):
            return distributed_gpt_pb2.JobResponse(status=JobStatus.FAIL, response=None)
        
        # lazily update the job status if all of the workers have responded
        if (None not in self.job_id_to_response[request.ticket].values()):
            self.job_request_status[request.ticket] = JobStatus.COMPLETED.value
            response = self.job_id_to_response[request.ticket]
        else:
            self.job_request_status[request.ticket] = JobStatus.PENDING.value
            response = None
                
        return distributed_gpt_pb2.JobResponse(status=self.job_id_to_response[request.ticket].status, response=response)

    def giveAgentAssignment(self, request, context):
        agent_state = self.assoc_interface.get_agent_state(self.proc_id_counter)
        args = vars(agent_state)
        args['user_id'] = str(args['user_id'])
        args['id'] = str(args['id'])
        args['llm_config'] = vars(args['llm_config'])
        args['embedding_config'] = vars(args['embedding_config'])
        
        args.pop("created_at", None) 
        for function in args['state']['functions']:
            for property in function['parameters']['properties']:
                function['parameters']['properties'][property] = distributed_gpt_pb2.PropertyDescription(**function['parameters']['properties'][property])
                
        self.assoc_interface.lock.acquire()
        self.proc_id_counter += 1
        # add persona to the interface
        self.persona_dict[self.proc_id_counter] = args['persona']
        self.assoc_interface.lock.release()
        
        log(
            f"(SERVER) Assigned ID {self.proc_id_counter} to client with identity {context.peer()}!", 
            Logging.INFO.value
        )

        return distributed_gpt_pb2.Assignment(process_id=self.proc_id_counter, agent_state=distributed_gpt_pb2.AgentState(**args))
      
    def giveAgentMessage(self, request: distributed_gpt_pb2.TaskRequest, context):
        # pluck the message from the queue
        log(f'(SERVER) Plucking a message out to give to agent {request.id}', Logging.INFO.value)
        agent_message = self.assoc_interface.get_outgoing(request.id)
        return distributed_gpt_pb2.Task(src_id=agent_message.src_id, content=agent_message.content)
    
    def processAgentMessage(self, request: distributed_gpt_pb2.AgentMessage, context):

        log(f"(SERVER) Got a message from agent {request.src_id}", Logging.INFO.value)
        
        # this message is a response to the leader's dispatch of a task
        # if (request.dst_id == 0):
        #     map = self.job_id_to_response[request.job_id]
        #     map[request.src_id] = request.content
        # else: # this message is intended for another worker
        #     self.assoc_interface.push_message(request)
        self.assoc_interface.push_message(request)

        return distributed_gpt_pb2.Status(content="OK!")
    
    def sayGoodbye(self, request: distributed_gpt_pb2.GoodbyeMessage, context):
       self.assoc_interface.ack_goodbye(request.id) 
       return distributed_gpt_pb2.Status(content="OK!")


class PoolRPCInterface(PoolInterface):
    def __init__(self, N: int, addr: str, port: int):
        self.N = N
        # let's set up the rpc
        self.rpc = None
        self.addr = addr
        self.port = port
        self.lock = Lock()
        self.conn_addr = f"{self.addr}:{self.port}"
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        # messages from agent to leader
        self.agent_msg_queue: Queue[distributed_gpt_pb2.AgentMessage] = Queue(maxsize=100)
        # Queue<mapping, JobRequest>
        self.jobs_queue : Queue[Tuple[int, dict, distributed_gpt_pb2.JobRequest]] = Queue(maxsize=100)
        self.goodbyes : Queue[int] = Queue(maxsize=100)
        for i in range(1, N+1):
            self.goodbyes.put(i)
            
        self.locks: Dict[ProcessID, Lock] = {
            i: Lock() for i in range(1, self.N + 1)
        }

        # leader to agent message queue
        self.out_msg_queue: Dict[ProcessID, Queue[distributed_gpt_pb2.AgentMessage]] \
            = {i: Queue(maxsize=100) for i in range(1, self.N + 1)}
        
        try:
            distributed_gpt_pb2_grpc.add_LeaderServicer_to_server(LeaderServicer(self), self.server)
        except Exception as e:
            print(f"Failed to add servicer: {e}")
        
        # Populate this with the agent personas
        self.agent_personas : Dict[ProcessID, str] = {}
        
        self.server.add_insecure_port(self.conn_addr)
        self.server.start()
        log("(SERVER) Started server!", Logging.IMPORTANT.value)

    def _broadcast(self, msg: dict) -> Status:
        for i in range(1, self.N + 1):
            msg.update({"dst_id": i})
            self._send_message(
                AgentMessage(
                    _raw = msg, src_id=msg['src_id'], dst_id=msg['dst_id'], 
                    job_id=msg['job_id'], content=msg['content']
                )
            )

        return {}
    
    def _send_message(self, msg: AgentMessage) -> Status:
        msg_obj = distributed_gpt_pb2.AgentMessage(
            src_id = msg.src_id, dst_id=msg.dst_id, job_id=msg.job_id, content=msg.content
        )
        self.out_msg_queue[msg.dst_id].put(msg_obj)

        log(
            f"(SERVER) Put a msg from agent {msg.src_id} addressed to agent {msg.dst_id} in queue!", 
            Logging.INFO.value
        )
        return {}
        
    def _recv(self) -> List[object]:
        return {}
    
    def start_processes(self) -> None:
        pass
    
    def join_processes(self) -> None:
        self.goodbyes.join()
        log("(SERVER) Ok! All clients have closed. I can close now.", Logging.INFO.value)

    
    ##### PoolRPCInterface specific methods #####
    
    def dispatch_job(self):
        job : Tuple[int, dict, distributed_gpt_pb2.JobRequest] = self.jobs_queue.get()
        job_id = job[0]
        document_to_agent_mapping = json.loads(job[1])
        job_request = job[2]
        # for each document(k) to agent(v) mapping
        for k,v in document_to_agent_mapping.items():
            k = int(k)
            v = int(v)
            content = LEADER_TO_WORKER_PROLOGUE + job_request.files[k]
            agent_message = distributed_gpt_pb2.AgentMessage(
                src_id=0, dst_id=v, job_id=job_id, content=content
            )
            self._send_message(agent_message)

    def get_agent_state(self, i):
        agent_states = MultiAgentCustodian.init().list_multi_agents()
        return agent_states[i]
    
    def close_server(self):
        log("(SERVER) Closing server!", Logging.IMPORTANT, attrs = ['bold'])
        self.server.stop(grace=10)
    
    def get_outgoing(self, proc_id: ProcessID) -> distributed_gpt_pb2.AgentMessage:
        
        msg_available = False
        while self.out_msg_queue[proc_id].empty():
            if msg_available == False:
                log(f"(SERVER) There is no message for: {proc_id}...", Logging.INFO.value)
                msg_available = True
                
        log(f"(SERVER) Plucked message for agent {proc_id}", Logging.INFO.value)
        self.locks[proc_id].acquire()
        outgoing = self.out_msg_queue[proc_id].get()
        self.locks[proc_id].release()
        return outgoing
        
    def _recv_any(self) -> object:
        while self.agent_msg_queue.empty():
            # busy wait lol
            continue

        msg = self.agent_msg_queue.get()

        log("(SERVER) I can pull a message from the message queue!", Logging.INFO.value)
        log(f"The message is from {msg.src_id} to {msg.dst_id}", Logging.INFO.value)
    
        return msg
    
    def push_message(self, msg: distributed_gpt_pb2.AgentMessage):
        self.agent_msg_queue.put(msg)
    
    def ack_goodbye(self, process_id: ProcessID):
        self.goodbyes.get()
        self.goodbyes.task_done()