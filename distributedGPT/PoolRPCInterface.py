from __future__ import annotations
from typing import List, Deque, Dict
from PoolInterface import PoolInterface
from concurrent import futures
from Custodian import MultiAgentCustodian
from collections import deque
from messages import AgentMessage

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
        # self.assoc_pool = assoc_pool

    def giveAgentAssignment(self, request, context):
        agent_state = self.assoc_interface.get_agent_state()
        args = vars(agent_state)
        args['user_id'] = str(args['user_id'])
        args['id'] = str(args['id'])
        # args.pop("llm_config", None)
        args['llm_config'] = vars(args['llm_config'])
        args['embedding_config'] = vars(args['embedding_config'])
        

        args.pop("created_at", None) 
        for function in args['state']['functions']:
            for property in function['parameters']['properties']:
                function['parameters']['properties'][property] = distributed_gpt_pb2.PropertyDescription(**function['parameters']['properties'][property])
                
        self.proc_id_counter += 1
        return distributed_gpt_pb2.Assignment(process_id=self.proc_id_counter, agent_state=distributed_gpt_pb2.AgentState(**args))
    
    def giveAgentMessage(self, request: distributed_gpt_pb2.TaskRequest, context):
        # pluck the message from the queue
        print(f'plucking a message out to give to agent {request.id}')
        agent_message = self.assoc_interface.get_outgoing(request.id)
        # print(f"(server) sending the following message to agent {agent_message.dst_id} from agent {agent_message.src_id} :\n\n", agent_message.content)
        return distributed_gpt_pb2.Task(src_id=agent_message.src_id, content=agent_message.content)
    
    def processAgentMessage(self, request: distributed_gpt_pb2.AgentMessage, context):
        self.assoc_interface.push_message(request)
        print(f"got a message from agent {request.src_id}\n")
        return distributed_gpt_pb2.Status(content="OK!")


class PoolRPCInterface(PoolInterface):
    def __init__(self, N: int):
        self.N = N
        # let's set up the rpc
        self.rpc = None
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self.agent_msg_queue: Deque[distributed_gpt_pb2.AgentMessage] = deque(maxlen=100)
        self.out_msg_queue: Dict[ProcessID, Deque[distributed_gpt_pb2.AgentMessage]] \
            = {i : deque(maxlen=100) for i in range(1, self.N + 1)}
        
        distributed_gpt_pb2_grpc.add_LeaderServicer_to_server(LeaderServicer(self), self.server)
        # TODO: do not hardcode the port
        self.server.add_insecure_port("[::]:50051")
        self.server.start()
        print("Started server!")

    def _broadcast(self, msg: dict) -> Status:
        for i in range(1, self.N + 1):
            msg.update({"dst_id": i})
            self._send_message(AgentMessage(_raw = msg, src_id=msg['src_id'], dst_id=msg['dst_id'], content=msg['content'])) 

        return {}
    
    def _send_message(self, msg: AgentMessage) -> Status:
        msg_obj = distributed_gpt_pb2.AgentMessage(src_id = msg.src_id, dst_id=msg.dst_id, content=msg.content)
        self.out_msg_queue[msg.dst_id].append(msg_obj)
        print(f"put a message from agent {msg.src_id} addressed to agent {msg.dst_id} in queue!")
        return {}
        
    def _recv(self) -> List[object]:
        return {}
    
    def start_processes(self) -> None:
        pass
    
    def join_processes(self) -> None:
        pass
    
    ##### PoolRPCInterface specific methods #####

    def get_agent_state(self):
        agent_states = MultiAgentCustodian.init().list_multi_agents()
        return agent_states[0]    
    
    def close_server(self):
        
        print("Closing server!")
        self.server.stop(grace=10)
    
    def get_outgoing(self, proc_id: ProcessID) -> distributed_gpt_pb2.AgentMessage:
        while len(self.out_msg_queue[proc_id]) == 0: continue
        return self.out_msg_queue[proc_id].popleft()
        
    def _recv_any(self) -> object:
        while len(self.agent_msg_queue) == 0:
            # busy wait lol
            # print("(server) waiting for a message to process...")
            continue
        print("(server) i can pull a message from the message queue!")
        return self.agent_msg_queue.popleft()
    
    def push_message(self, msg: distributed_gpt_pb2.AgentMessage):
        self.agent_msg_queue.append(msg)
    