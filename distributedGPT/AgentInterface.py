from __future__ import annotations
from typing import Annotated, List, Tuple, Dict, Any, Union
from memgpt.interface import AgentInterface
import multiprocessing as mp
from multiprocessing.connection import Connection
from dataclasses import dataclass
import uuid
import json
from messages.Message import Message
from grpc_driver.grpc_client import distributedGPTClient

class AgentPipeInterface(AgentInterface):
    """
    In an AgentPipeInterface, we want to communicate everything via bidirectional pipes. 
    There will be pipes running from each agent to each other, as well as from an agent to main
    process. Internally, an AgentPipeInterface maintains the interface for an agent.
    
    Inherits from the MemGPTAgentInterface class.
    """
    
    def __init__(self, pipe: Connection):
        """
        pipe: this is a pipe that lets us talk to the main process
        """
        self.pipe = pipe
        # this attribute symbolizes the most recent mes
        self.message = None
    
    def user_message(self, msg: str, msg_obj: Message | None = None):
        print("Calling user_message")
    
    def internal_monologue(self, msg: str, msg_obj: Message | None = None):
        print("Calling internal_monologue")
    
    def assistant_message(self, msg: str, msg_obj: Message | None = None):
        print("Sending data to leader")
        # self.pipe.send(msg)
        print("Sent")

    def function_message(self, msg: str, msg_obj: Message | None = None):
        print("Calling a function!")
    
    ################### AgentPipeInterface specific methods! ###################
    def get_message(self) -> Any:
        """Wait for the main process to send a message, and process it"""
        message = self.pipe.recv()
        return message
    
    def write_message(self, msg) -> None:
        self.pipe.send(msg)
    
    def close(self):
        self.pipe.close()
        
    def __del__(self):
        """When the interface is being torn down, close all the pipes"""


class RPCAgentInterface(AgentInterface):
    def __init__(self, RPCclient: distributedGPTClient):
        """
        pipe: this is a pipe that lets us talk to the main process
        """
        self.RPCclient = RPCclient
        # this attribute symbolizes the most recent mes
        self.message = None
    
    def user_message(self, msg: str, msg_obj: Message | None = None):
        print("Calling user_message")
    
    def internal_monologue(self, msg: str, msg_obj: Message | None = None):
        print("Calling internal_monologue")
    
    def assistant_message(self, msg: str, msg_obj: Message | None = None):
        print("Calling assistant_message")
    
    def function_message(self, msg: str, msg_obj: Message | None = None):
        print("Calling a function!") 
        
    ################### RPCAgentInterface specific methods! ###################
    