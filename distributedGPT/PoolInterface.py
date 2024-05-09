from __future__ import annotations
from typing import Annotated, List, Tuple, Dict, Any, Union
from memgpt.interface import AgentInterface
import multiprocessing as mp
from multiprocessing.connection import Connection
from dataclasses import dataclass
import uuid
from collections import deque
import json
from messages.Message import Message
from abc import ABC, abstractmethod
from memgpt.config import MemGPTConfig
from memgpt.metadata import MetadataStore
import memgpt.system
from Custodian import MultiAgentCustodian
from ProcessAgent import ProcessAgent, StepResponse
from AgentInterface import AgentPipeInterface

Status = dict

class PoolInterface(ABC):
    @abstractmethod
    def _broadcast(self, msg: str) -> Status:
        raise NotImplementedError
    
    @abstractmethod
    def _send_message(self, msg: str, dst_id: int) -> Status:
        raise NotImplementedError
    
    @abstractmethod
    def _recv(self) -> List[object]:
        raise NotImplementedError
    
    @abstractmethod
    def start_processes(self) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def join_processes(self) -> None:
        raise NotImplementedError

class PoolPipeInterface(PoolInterface):
    def __init__(self, N: int):
        self.N = N
        self._pipes = [mp.Pipe() for _ in range(self.N)]
        self._parent_conns = [pipe[0] for pipe in self._pipes]
        
        # TODO: generalize this?
        # get the agents from the custodian (for now)
        agent_states = MultiAgentCustodian.init().list_multi_agents()
        print(agent_states[0].state['functions'][0]['parameters'])
        exit()
        self.agents = [ProcessAgent(i+1, agent_states[i], AgentPipeInterface(self.get_agent_conns()[i])) for i in range(N)]
        self.processes = [mp.Process(target=ProcessAgent.event_loop, args=(self.agents[i],)) for i in range(N)]
        
    def _broadcast(self, msg: str) -> Status:
        try:
            for pipe in self.get_parent_conns():
                pipe.send(msg)
            return {"status": "Ok"}
        except Exception as e:
            raise Exception(e)
   
    def _send_message(self, msg: str, dst_id: int) -> Status:
        assert dst_id < self.N, f"target agent_id must be in interval [0, {self.N})" 
        try:
            pipe = self.get_parent_conns()[dst_id]
            pipe.send(msg)
            return {"status": "Ok"}
        except Exception as e:
            raise Exception(e)
        
    def _recv(self) -> List[object]:
        status = [None for _ in range(self.N)]
        for i in range(self.N):
            pipe = self._parent_conns[i]
            status[i] = pipe.recv()
        return status
    
    def _recv_any(self) -> object:
        i = 0
        while True:
            pipe = self._parent_conns[i]
            if pipe.poll():
                return pipe.recv()
            i = (i + 1) % self.N 
    
    def start_processes(self) -> None:
        for i in range(self.N):
            self.processes[i].start()

    def join_processes(self) -> None:
        for i in range(self.N):
            self.processes[i].join()    
        
    def __del__(self):
        """When the interface is being torn down, close all the pipes"""
        
    ################### PoolPipeInterface specific methods! ##################################
    def get_parent_conns(self) -> List[Connection]:
        return self._parent_conns
    
    def get_agent_conns(self) -> List[Connection]:
        return [pipe[1] for pipe in self._pipes]
 
 
# class PoolRPCInterface(PoolInterface):
#     def __init__(self, N: int):
#         self.N = N
#         ''' what type of information does leader need to know / 
#         things that come to mind:
#         1) worker-worker relationships (perhaps a map of clientid->clientid)
#         '''
#         self.job_queue = deque(maxlen=10)
#         self.rpc = DistributedGPTLeader(self) 
   

#     def _broadcast(self, msg: str) -> Status:
#         pass
    
    
#     def _send_message(self, msg: str, dst_id: int) -> Status:
#         pass
    
    
#     def _recv(self) -> List[object]:
#         pass
    
    
#     def start_processes(self) -> None:
#         pass
    
    
#     def join_processes(self) -> None:
#         pass
   
#     def test(self):
#         self.rpc.test()