from __future__ import annotations
from typing import Annotated, List, Tuple, Dict, Any, Union
from memgpt.agent import Agent, AgentState
from memgpt.config import MemGPTConfig
from memgpt.metadata import MetadataStore
from memgpt.data_types import Message
from memgpt.interface import AgentInterface
import multiprocessing as mp
from multiprocessing.connection import Connection
from dataclasses import dataclass
from memgpt.utils import get_local_time
from memgpt.constants import JSON_ENSURE_ASCII, FUNC_FAILED_HEARTBEAT_MESSAGE, REQ_HEARTBEAT_MESSAGE
import uuid
from messages.PoolMessage import PoolMessage
from ProcessAgent import ProcessAgent, StepResponse
from PoolInterface import PoolInterface, PoolPipeInterface

import json
from enum import Enum
Status = dict

class InterfaceTypes(Enum):
    PIPE = "pipe"
    RPC  = "rpc"

class AgentPool:
    @staticmethod
    def event_loop(pool: AgentPool):
        should_terminate = False
        while not should_terminate:
            data_for_agent_one = {
                "src_id": 0,
                "content": "What is your name?"
            }

            data_for_agent_two = {
                "src_id": 1,
                "content": "What is your name? Please address your response to me!"
            }
            
            pool.send(json.dumps(data_for_agent_one), 0)
            # pool.send(json.dumps(data_for_agent_two), 1)
            results : List[StepResponse] = pool.recv()
            for result in results:
                result.pprint_agent_message() 
            break
            
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
        
    
if __name__ == "__main__":
    agent_pool = AgentPool(2)
    