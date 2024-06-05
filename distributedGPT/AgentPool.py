from __future__ import annotations
from typing import Annotated, List, Tuple, Dict, Any, Union
import multiprocessing as mp
from messages import AgentMessage
import random
from PoolInterface import PoolPipeInterface
from PoolRPCInterface import PoolRPCInterface
from google.protobuf.json_format import MessageToDict
from termcolor import colored

from enum import Enum

Status = dict

class InterfaceTypes(Enum):
    PIPE = "pipe"
    RPC  = "rpc"




class AgentPool:
    
    @staticmethod
    def event_loop(pool: AgentPool):
        should_terminate = False
        i = 0
        print("I'm about to enter the event loop")
        while not should_terminate:
            result = pool.recv_any()
            result : AgentMessage = AgentMessage(_raw=MessageToDict(result, always_print_fields_with_no_presence=True), content=result.content, src_id=result.src_id, dst_id=result.dst_id)
            print()
            print(colored(f"Message from agent {result.src_id}:", "green", attrs=["bold"]))
            result.pprint_message()
            print()

            
            
    def __init__(self, N: Annotated[int, "num memgpt agents"], interface_type: InterfaceTypes, **interface_kwargs):
        # spawn N processes
        self.N = N
        # main process ALWAYS has ID of 0
        self.id = 0
        if interface_type == InterfaceTypes.PIPE:
            self.interface = PoolPipeInterface(self.N, **interface_kwargs)
        elif interface_type == InterfaceTypes.RPC:
            self.interface = PoolRPCInterface(self.N, **interface_kwargs)
        else:
            raise NotImplementedError
        self.interface.start_processes()
        AgentPool.event_loop(self)
        self.interface.join_processes()
    
    def broadcast(self, msg: str) -> Status:
        """broadcast() sends some message to all agent processes; returns status"""
        return self.interface._broadcast(msg)
        
    def send(self, msg:str) -> Status:
        return self.interface._send_message(msg)
    
    def recv(self) -> List[object]:
        return self.interface._recv()
    
    def recv_any(self) -> List[object]:
        return self.interface._recv_any()
    
    
if __name__ == "__main__":
    agent_pool = AgentPool(1, InterfaceTypes.RPC)
    