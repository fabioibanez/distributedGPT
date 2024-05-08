from __future__ import annotations
from typing import Annotated, List, Tuple, Dict, Any, Union
import multiprocessing as mp
from messages import AgentMessage
from PoolInterface import PoolInterface, PoolPipeInterface

import json
from enum import Enum

Status = dict

class InterfaceTypes(Enum):
    PIPE = "pipe"
    RPC  = "rpc"

class AgentPool:
    STOP_MSG = {"src_id": 0, "content": "STOP"}
    @staticmethod
    def event_loop(pool: AgentPool):
        should_terminate = False
        outgoing_msg = {
            "src_id": 2,
            "content": "What is your name? And could you tell me more about yourself?"
        }
        pool.send(json.dumps(outgoing_msg), 0)
        i = 0
        while not should_terminate:

            # the pool waits for any of the agents to send something
            result : dict = pool.recv_any()
            result : AgentMessage = AgentMessage(_raw=result, content=result['content'], src_id=result['src_id'], dst_id=result['dst_id'])
            result.pprint_message() 
            # relay the message
            outgoing_msg = {'src_id': result.src_id, "content": result.content}
            
            # print(f'sending outgoing_msg {outgoing_msg} \n\nto agent with PROC ID {result.dst_id}')
            i += 1
            if i >= 5:
                pool.broadcast(AgentPool.STOP_MSG)
                break
            else:
                pool.send(json.dumps(outgoing_msg), result.dst_id - 1)
            
            
    def __init__(self, N: Annotated[int, "num memgpt agents"], interface_type: InterfaceTypes):
        # spawn N processes
        self.N = N
        # main process ALWAYS has ID of 0
        self.id = 0

        if interface_type == InterfaceTypes.PIPE:
            self.interface = PoolPipeInterface(self.N)
        else:
            raise NotImplementedError
    
        self.interface.start_processes()
        AgentPool.event_loop(self)
        self.interface.join_processes()
    
    def broadcast(self, msg: str) -> Status:
        """broadcast() sends some message to all agent processes; returns status"""
        return self.interface._broadcast(msg)
        
    def send(self, msg:str, dst_id: int) -> Status:
        return self.interface._send_message(msg, dst_id)
    
    def recv(self) -> List[object]:
        return self.interface._recv()
    
    def recv_any(self) -> List[object]:
        return self.interface._recv_any()
        
    
if __name__ == "__main__":
    agent_pool = AgentPool(1)
    