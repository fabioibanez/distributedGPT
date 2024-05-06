from __future__ import annotations
from typing import Annotated, List, Tuple, Dict, Any, Union
from memgpt.agent import Agent, AgentState
from memgpt.config import MemGPTConfig
from memgpt.metadata import MetadataStore
from memgpt.data_types import Message
from memgpt.interface import AgentInterface
import memgpt.system
import multiprocessing as mp
from multiprocessing.connection import Connection
from dataclasses import dataclass
from memgpt.utils import get_local_time
from memgpt.constants import JSON_ENSURE_ASCII, FUNC_FAILED_HEARTBEAT_MESSAGE, REQ_HEARTBEAT_MESSAGE
import uuid
import json


@dataclass
class StepResponse:

    new_messages: Union[List[str], str] 
    user_message: str
    skip_next_user_input: str
    
    def pprint_agent_message(self) -> None:
        from pygments import highlight
        from pygments.formatters.terminal256 import Terminal256Formatter
        from pygments.lexers.web import JsonLexer
        json_str = json.dumps(self.new_messages, indent=2, sort_keys=True)
        colorful = highlight(json_str, lexer=JsonLexer(), formatter=Terminal256Formatter())
        print(colorful) 



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
    
    def close(self):
        self.pipe.close()
        
    def __del__(self):
        """When the interface is being torn down, close all the pipes"""
 

# TODO:
# 1). Monotonically increasing ID for each message
# 2). Some IDs unique to each leader-worker pair
# 3). Having identifiers of src/recipients 
# 4). A timestamp would be great
# 5). 
 
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

@dataclass 
class PoolMessage(Message):
    pass

class MessageFactory:

    @staticmethod
    def create_agent_input(msg: Message) -> str:
        formatted_time = get_local_time()
        packaged_message = {
            "type": "agent_message",
            "message": msg,
            "time": formatted_time,
        }
        return json.dumps(packaged_message, ensure_ascii=JSON_ENSURE_ASCII)
        
    
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

            msg = MessageFactory.create_agent_input(agent.message)
            response = agent.respond(msg)
            
            agent.write_to_main(response)
            break

    @staticmethod
    def process_agent_step(agent: ProcessAgent, user_message, no_verify = False):
        new_messages, heartbeat_request, function_failed, token_warning, tokens_accumulated = agent.step(
            user_message,
            first_message=False,
            skip_verify=no_verify,
            stream=False,
        )

        skip_next_user_input = False
        if token_warning:
            user_message = memgpt.system.get_token_limit_warning()
            skip_next_user_input = True
        elif function_failed:
            user_message = memgpt.system.get_heartbeat(FUNC_FAILED_HEARTBEAT_MESSAGE)
            skip_next_user_input = True
        elif heartbeat_request:
            user_message = memgpt.system.get_heartbeat(REQ_HEARTBEAT_MESSAGE)
            skip_next_user_input = True

        return new_messages, user_message, skip_next_user_input
    
    
    def __init__(self, agent_state: AgentState, pipe: Connection):
        interface = PipeInterface(pipe)
        super().__init__(interface=interface, agent_state=agent_state)
        # this symbolizes the most recent message that the agent has received from main process
        self.message = None
        # doing this weird no-op initialization to get type hinting
        self.interface : PipeInterface = self.interface
    
    def respond(self, msg) -> StepResponse:
        new_messages, user_message, skip_next_user_input = ProcessAgent.process_agent_step(self, msg, False)
        return StepResponse(new_messages, user_message, skip_next_user_input)
    
    def read_from_main(self) -> None:
        # stateful method that will update the message attribute to the latest message sent by main process
        self.message = self.interface.get_message()
    
    def write_to_main(self, msg) -> None:
        self.interface.write_message(msg)
    
    
    def __del__(self):
        self.interface.close()

Status = dict

class AgentPool:
    
    @staticmethod
    def event_loop(pool: AgentPool):
        should_terminate = False
        while not should_terminate:
            # status  = pool.broadcast("Hi!")
            pool.send("What is the average weather in Miami, Florida over the month of June?", 0)
            pool.send("What is the average weather in Queens, New York over the month of June?", 1)
            results : List[StepResponse] = pool.recv()
            for result in results:
                result.pprint_agent_message() 
            break
            
    
    def __init__(self, N: Annotated[int, "num memgpt agents"]):
        # spawn N processes
        self.N = N
        # main process ALWAYS has ID of 0
        self.id = 0
        
        # let's fetch all agent states in our metadata store
        config = MemGPTConfig()
        ms = MetadataStore(config)
        user_id = uuid.UUID(config.anon_clientid)
        agent_states = ms.list_agents(user_id)
        pipes : List[Tuple[Connection]] = [mp.Pipe() for _ in range(N)]
        # interfaces: List[PipeInterface] = [PipeInterface(pipes[i]) for i in self.N]
        self.parent_conns = [pipe[0] for pipe in pipes]

        self.agents    = [ProcessAgent(agent_states[i], pipes[i][1]) for i in range(N)]
        self.processes = [
            mp.Process(target=ProcessAgent.event_loop, args=(self.agents[i], )) for i in range(N)
        ]

        for i in range(len(self.processes)):
            self.processes[i].start()
            
        AgentPool.event_loop(self)
        for i in range(len(self.processes)):
            self.processes[i].join()
        
        # self.agents = [ProcessAgent()]
        # # each agent will be effectively a process on the machine
        # self.processes = [mp.Process(target=ProcessAgent.event_loop, )]
    
    def broadcast(self, msg: str) -> Status:
        """broadcast() sends some message to all agent processes"""
        try:
            for pipe in self.parent_conns:
                pipe.send(msg)
            return {"status": "Ok"}
        except Exception as e:
            raise Exception(e)
    
    def send(self, msg:str, dst_id: int):
        assert dst_id < self.N, f"target agent_id must be in interval [0, {self.N})" 
        try:
            pipe = self.parent_conns[dst_id]
            pipe.send(msg)
            return {"status": "Ok"}
        except Exception as e:
            raise Exception(e)
    
    def recv(self) -> List[object]:
        status = [None for _ in range(self.N)]
        for i in range(self.N):
            pipe = self.parent_conns[i]
            status[i] = pipe.recv()
        return status
    
class MultiAgentCustodian:
    """
    This custodian object takes care of behind-the-scene details involved with making MemGPT
    work in a multi-agent fashion. This includes implementating mechanisms to allow the end user to
    update the multi-agent system prompt, for instance.
    
    Essentially, the custodian allows us to rapidly experiment + visualize what's going on in the multi
    agent system (think: custodians clean up the mess left behind, and have the keys to any needed privileged access).
    
    A given custodian object does not need to hold any particular state. Concretely, there is only
    ever a singleton custodian object. We do this because we can determine that priviliged edits to any component of 
    our system comes from methods being called by this singleton object.
    """

    @dataclass
    class CustodianKnowledge:
        config: MemGPTConfig
        metadata_store: MetadataStore
    
    _custodian = None
    
    def __init__(self, *args, **kwargs):
        raise NotImplementedError
        
    @classmethod
    def init(cls):
        if cls._custodian is None:
            cls._custodian = super().__new__(cls)

        cls._custodian.state = MultiAgentCustodian.CustodianKnowledge(MemGPTConfig.load(), MetadataStore(MemGPTConfig.load()))

        return cls._custodian
        
    @staticmethod
    def replace_multi_system_prompt(new_prompt: str):
        # get the ms store that custodian has access to
        ms : MetadataStore = MultiAgentCustodian._custodian.state.metadata_store
        ms.update
     
    
    
    
    
if __name__ == "__main__":
    agent_pool = AgentPool(2)
    