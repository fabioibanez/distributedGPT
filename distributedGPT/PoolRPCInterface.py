from __future__ import annotations
from typing import List
from PoolInterface import PoolInterface
from concurrent import futures
from Custodian import MultiAgentCustodian
import grpc
import distributed_gpt_pb2_grpc
import distributed_gpt_pb2
from dataclasses import dataclass

Status = dict

class LeaderServicer(distributed_gpt_pb2_grpc.LeaderServicer):
    def __init__(self, assoc_interface: PoolRPCInterface):
        super().__init__()
        self.assoc_interface = assoc_interface
        # self.assoc_pool = assoc_pool

    def getAgentAssignment(self, request, context):
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


        return distributed_gpt_pb2.Assignment(process_id=0, agent_state=distributed_gpt_pb2.AgentState(**args))


class PoolRPCInterface(PoolInterface):
    def __init__(self, N: int):
        # let's set up the rpc
        self.rpc = None
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        distributed_gpt_pb2_grpc.add_LeaderServicer_to_server(LeaderServicer(self), self.server)
        # TODO: do not hardcode the port
        self.server.add_insecure_port("[::]:50051")
        self.server.start()
        print("Started server!")
        self.server.wait_for_termination() 

    def _broadcast(self, msg: str) -> dict:
        return {}
    
    def _send_message(self, msg: str, dst_id: int) -> Status:
        return {}
    
    def _recv(self) -> List[object]:
        return {}
    
    def start_processes(self) -> None:
        raise NotImplementedError
    def join_processes(self) -> None:
        return super().join_processes() 
    
    ##### PoolRPCInterface specific methods #####

    def get_agent_state(self):
        agent_states = MultiAgentCustodian.init().list_multi_agents()
        return agent_states[0]    
    
    def close_server(self):
        
        print("Closing server!")
        self.server.stop(grace=10)