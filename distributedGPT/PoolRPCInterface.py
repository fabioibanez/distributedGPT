from __future__ import annotations
from typing import List, Deque, Dict, Set
from PoolInterface import PoolInterface
from concurrent import futures
from Custodian import MultiAgentCustodian
from collections import deque
from queue import Queue
from messages import AgentMessage
from termcolor import colored

import grpc
import distributed_gpt_pb2_grpc
import distributed_gpt_pb2

Status = dict
ProcessID = int

class LeaderServicer(distributed_gpt_pb2_grpc.LeaderServicer):
    def __init__(self, assoc_interface: PoolRPCInterface):
        super().__init__()
        self.assoc_interface = assoc_interface
        self.proc_id_counter = 0

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
                
        self.proc_id_counter += 1
        print()
        print(colored(f"(SERVER) Assigned ID {self.proc_id_counter} to client with identity {context.peer()}!", "light_grey"))
        print()
        return distributed_gpt_pb2.Assignment(process_id=self.proc_id_counter, agent_state=distributed_gpt_pb2.AgentState(**args))
    
    def giveAgentMessage(self, request: distributed_gpt_pb2.TaskRequest, context):
        # pluck the message from the queue
        print()
        print(colored(f'(SERVER) Plucking a message out to give to agent {request.id}', 'light_grey'))
        print()
        agent_message = self.assoc_interface.get_outgoing(request.id)
        # print(f"(server) sending the following message to agent {agent_message.dst_id} from agent {agent_message.src_id} :\n\n", agent_message.content)
        return distributed_gpt_pb2.Task(src_id=agent_message.src_id, content=agent_message.content)
    
    def processAgentMessage(self, request: distributed_gpt_pb2.AgentMessage, context):
        self.assoc_interface.push_message(request)
        print()
        print(colored(f"(SERVER) Got a message from agent {request.src_id}", 'light_grey'))
        print()
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
        self.conn_addr = f"{self.addr}:{self.port}"
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self.agent_msg_queue: Queue[distributed_gpt_pb2.AgentMessage] = Queue(maxsize=100)
        self.goodbyes : Queue[int] = Queue(maxsize=100)
        for i in range(1, N+1):
            self.goodbyes.put(i)

        self.out_msg_queue: Dict[ProcessID, Queue[distributed_gpt_pb2.AgentMessage]] \
            = {i: Queue(maxsize=100) for i in range(1, self.N + 1)}
        
        distributed_gpt_pb2_grpc.add_LeaderServicer_to_server(LeaderServicer(self), self.server)
        # TODO: do not hardcode the port
        self.server.add_insecure_port(self.conn_addr)
        self.server.start()
        print() 
        print(colored("(SERVER) Started server!", "light_grey"))
        print()

    def _broadcast(self, msg: dict) -> Status:
        for i in range(1, self.N + 1):
            msg.update({"dst_id": i})
            self._send_message(AgentMessage(_raw = msg, src_id=msg['src_id'], dst_id=msg['dst_id'], content=msg['content'])) 

        return {}
    
    def _send_message(self, msg: AgentMessage) -> Status:
        msg_obj = distributed_gpt_pb2.AgentMessage(src_id = msg.src_id, dst_id=msg.dst_id, content=msg.content)
        self.out_msg_queue[msg.dst_id].put(msg_obj)

        print()
        print(colored(f"(SERVER) Put a message from agent {msg.src_id} addressed to agent {msg.dst_id} in queue!", "light_grey"))
        print()
        return {}
        
    def _recv(self) -> List[object]:
        return {}
    
    def start_processes(self) -> None:
        pass
    
    def join_processes(self) -> None:
        self.goodbyes.join()
        print()
        print(colored("(SERVER) Ok! All clients have closed. I can close now.", "light_grey"))
        print()
    
    ##### PoolRPCInterface specific methods #####

    def get_agent_state(self, i):
        agent_states = MultiAgentCustodian.init().list_multi_agents()
        return agent_states[i]
    
    def close_server(self):
        print("(SERVER) Closing server!")
        self.server.stop(grace=10)
    
    def get_outgoing(self, proc_id: ProcessID) -> distributed_gpt_pb2.AgentMessage:
        msg_available = False
        while self.out_msg_queue[proc_id].empty():
            if msg_available == False:
                print()
                print(f"(SERVER) There is no message for: {proc_id}...")
                print()
                msg_available = True
        print()
        print(colored(f"(SERVER) Plucked message for agent {proc_id}", "light_grey"))
        print()
        outgoing = self.out_msg_queue[proc_id].get()
        return outgoing
        
    def _recv_any(self) -> object:
        while self.agent_msg_queue.empty():
            # busy wait lol
            continue

        msg = self.agent_msg_queue.get()
        print()
        print(colored("(SERVER) I can pull a message from the message queue!", "light_grey"))
        print(colored(f"The message is from {msg.src_id} to {msg.dst_id}", "light_grey"))
        print()
    
        return msg
    
    def push_message(self, msg: distributed_gpt_pb2.AgentMessage):
        self.agent_msg_queue.put(msg)
    
    def ack_goodbye(self, process_id: ProcessID):
        self.goodbyes.get()
        self.goodbyes.task_done()