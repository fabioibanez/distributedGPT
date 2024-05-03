from __future__ import annotations
from typing import Annotated, List, Tuple, Dict, Any
from memgpt.agent import Agent, AgentState
from memgpt.data_types import Message
from memgpt.interface import AgentInterface
import memgpt.system
import multiprocessing as mp
from multiprocessing.connection import Connection
from dataclasses import dataclass

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
        print("Calling user_message")
    
    def internal_monologue(self, msg: str, msg_obj: Message | None = None):
        print("Calling internal_monologue")
    
    def assistant_message(self, msg: str, msg_obj: Message | None = None):
        print("Calling assistant_message")
    
    def function_message(self, msg: str, msg_obj: Message | None = None):
        print("Calling a function!")
    
    ################### PipeInterface specific methods! ##################################
    def get_message(self) -> Any:
        """Wait for the main process to send a message, and process it"""
        message = self.pipe.recv()
        return message
    
    def write_message(self, msg) -> None:
        self.pipe.send(msg)
        
    def __del__(self):
        """When the interface is being torn down, close all the pipes"""
 
@dataclass
class Message:
    _raw: dict
    content: str
    
    @staticmethod
    def is_valid(raw):
        assert isinstance(raw, dict), "all messages must be dict-like"
        assert 'content' in raw, "all messages must have a `content` field for string content"
        
    @classmethod 
    def from_raw(cls, raw):
        Message.is_valid(raw)
        return cls(_raw = raw, content = raw['content'])

@dataclass
class AgentInput(Message):

    def is_valid(self):
        super().is_valid()

    @classmethod
    def from_raw(cls):
        pass

class MessageFactory:

    @staticmethod
    def create_agent_input(msg: Message) -> AgentInput:
        msg.conent 
        
    
class ProcessAgent(Agent):
    
    @staticmethod
    def event_loop(agent: ProcessAgent):
        """
        Main event loop of this process. We wait for input from main process, process it, and
        send a response back to the main process.
        """
        while True:
            # get the latest message available (will always be a new message by construction of while loop)
            agent.read_from_main()
            
            # TODO: add a validation routine here that makes sure message scheme is consistent
            # <validation routine call here> 
            
            # this message will be now parsed by the agent, who will give a response to be sent back
            # to the main process

            msg = memgpt.
            response = agent.respond(msg)
            
            agent.write_to_main(response)

    
    
    def __init__(self, agent_state: AgentState, pipe: Connection):
        interface = PipeInterface(pipe)
        super().__init__(interface=interface, agent_state=agent_state)
        # this symbolizes the most recent message that the agent has received from main process
        self.message = None
        # doing this weird no-op initialization to get type hinting
        self.interface : PipeInterface = self.interface
    
    def respond(self):
        
    
    def read_from_main(self) -> None:
        # stateful method that will update the message attribute to the latest message sent by main process
        self.message = self.interface.get_message()
    
    def write_to_main(self, msg) -> None:
        self.interface.write(msg)

class AgentPool:
    def __init__(self, N: Annotated[int, "num memgpt agents"]):
        # spawn N processes
        self.N = N
        # main process ALWAYS has ID of 0
        self.id = 0
        # each agent will be effectively a process on the machine
        pass