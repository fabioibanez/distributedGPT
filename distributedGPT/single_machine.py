from __future__ import annotations
from typing import Annotated, List, Tuple, Dict, Any
from memgpt.agent import Agent, AgentState
from memgpt.data_types import Message
from memgpt.interface import AgentInterface
import multiprocessing as mp
from multiprocessing.connection import Connection

class PipeInterface(AgentInterface):
    """
    In a PipeInterface, we want to communicate everything via bidirectional pipes. 
    There will be pipes running from each agent to each other, as well as from an agent to main
    process. Internally, a PipeInterface object maintains a list of pipes.
    """
    
    def __init__(self, pipe: Connection):
        """
        pipe: this is a pipe that lets us talk to the main process
        """
        self.pipe = pipe
        # this attribute symbolizes the most recent mes
        self.message = None
    
    def user_message(self, msg: str, msg_obj: Message | None = None):
        return super().user_message(msg, msg_obj)
    
    def internal_monologue(self, msg: str, msg_obj: Message | None = None):
        return super().internal_monologue(msg, msg_obj)
    
    def assistant_message(self, msg: str, msg_obj: Message | None = None):
        return super().assistant_message(msg, msg_obj)
    
    def function_message(self, msg: str, msg_obj: Message | None = None):
        print("Calling a function!")
    
    ################### PipeInterface specific methods! ##################################
    def get_message(self) -> Any:
        """Wait for the main process to send a message, and process it"""
        message = self.pipe.recv()
        return message
        
    def __del__(self):
        """When the interface is being torn down, close all the pipes"""
        
    
class ProcessAgent(Agent):
    
    @staticmethod
    def event_loop(agent: ProcessAgent):
        """
        Main event loop of this process. We wait for input from main process, process it, and
        send a response back to the main process.
        """
        
        while True:
            agent.get_message()
    
    def __init__(self, agent_state: AgentState, pipe: Connection):
        interface = PipeInterface(pipe)
        super().__init__(interface=interface, agent_state=agent_state)
        # this symbolizes the most recent message that the agent has received from main process
        self.message = None
        self.interface : PipeInterface = self.interface
    
    def read_new_message(self) -> None:
        # stateful method that will update the message attribute to the latest message sent by main process
        self.message = self.interface.get_message()

class AgentPool:
    def __init__(self, N: Annotated[int, "num memgpt agents"]):
        # spawn N processes
        self.N = N
        # main process ALWAYS has ID of 0
        self.id = 0
        # each agent will be effectively a process on the machine
        pass