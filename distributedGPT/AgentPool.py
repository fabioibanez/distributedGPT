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
from distributedGPT.messages.PoolMessage import PoolMessage
from distributedGPT.ProcessAgent import ProcessAgent, StepResponse
from distributedGPT.PoolInterface import PoolInterface, PoolPipeInterface

Status = dict

class AgentPool:
    @staticmethod
    def event_loop(pool: AgentPool):
        should_terminate = False
        while not should_terminate:
            pool.send("What is the average weather in Miami, Florida over the month of June?", 0)
            pool.send("What is the average weather in Queens, New York over the month of June?", 1)
            results : List[StepResponse] = pool.recv()
            for result in results:
                result.pprint_agent_message() 
            break
            
    def __init__(self, N: Annotated[int, "num memgpt agents"], interface: PoolInterface):
        # spawn N processes
        self.N = N
        # main process ALWAYS has ID of 0
        self.id = 0

        self.interface : PoolInterface = interface
    
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
    