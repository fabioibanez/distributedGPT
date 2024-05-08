from __future__ import annotations
from memgpt.agent import Agent, AgentState
from multiprocessing.connection import Connection
from memgpt.constants import JSON_ENSURE_ASCII, FUNC_FAILED_HEARTBEAT_MESSAGE, REQ_HEARTBEAT_MESSAGE
from messages.MessageFactory import MessageFactory
import memgpt.system
import json
from typing import List, Union
from dataclasses import dataclass
from memgpt.interface import AgentInterface
import grpc
import distributed_gpt_pb2
import distributed_gpt_pb2_grpc

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

class ProcessAgent(Agent):
    
    @classmethod
    def as_rpc_client(cls):
        # we put the fucking rpc client code here
        with grpc.insecure_channel("localhost:50051") as channel:
            stub = distributed_gpt_pb2_grpc.LeaderStub(channel)
            assignment_request = distributed_gpt_pb2.AssignmentRequest(id="0")
            result = stub.getAgentAssignment(assignment_request)
            print(result)
            
    
    def __init__(self, proc_id: int, agent_state: AgentState, interface: AgentInterface):
        """
        Requires a client to pass in the an AgentInterface instance 
        (i.e. AgentPipeInterface) to communicate with the main process/
        leader.

        Args:
            agent_state (AgentState): _description_
            interface (AgentInterface): _description_
        """
        super().__init__(interface=interface, agent_state=agent_state)
        # this symbolizes the most recent message that the agent has received from main process
        self.message = None
        self.proc_id = proc_id
        # doing this weird no-op initialization to get type hinting
        self.interface : AgentInterface = self.interface
    
    @staticmethod
    def event_loop(agent: ProcessAgent):
        """
        Main event loop of this process. We wait for input from main process, process it, and
        send a response back to the main process.
        """
        while True:
            # get the latest message available (will always be a new message by construction of while loop)
            agent.read_from_main()
            if isinstance(agent.message, dict) and agent.message['content'] == "STOP":
                break
            
            # TODO: add a validation routine here that makes sure message scheme is consistent
            # <validation routine call here> 
            
            # this message will be now parsed by the agent, who will give a response to be sent back
            # to the main process

            msg = MessageFactory.create_agent_input(agent.message)
            agent.respond(msg)
            
            # agent.write_to_main(response)

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