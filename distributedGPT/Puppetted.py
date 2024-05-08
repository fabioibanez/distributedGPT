from __future__ import annotations
"""
Task:

There will be two MemGPT agents running concurrently. We want these agents to talk to one another,
but perhaps it's too ambitious to get them to talk autonomously. Instead, what's gonna happen is that
one MemGPT Agent (let's call them the 'puppet') will speak to the other agent (let's call them the 'server')
on our behalf. Concretely, this involves the puppet asking us for an input message to send to the server.
The server should hopefully update its internals. 

Checkpoints
- 1) Get a puppet agent to ask human for input
- 2) Get a puppet and server running as two different processes
- 3) Relay the puppet's message to the server, and send back response to the user
"""

from memgpt.agent import Agent, AgentState
from memgpt.metadata import MetadataStore
from memgpt.config import MemGPTConfig
from memgpt.interface import CLIInterface
from memgpt.constants import FUNC_FAILED_HEARTBEAT_MESSAGE, REQ_HEARTBEAT_MESSAGE
import memgpt.system

import multiprocessing as mp

from typing import List, Union
import uuid, questionary
import json
from dataclasses import dataclass

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

class Puppet(Agent):
    @classmethod
    def from_agent_state(cls, agent_state: AgentState):
        return cls(interface=CLIInterface(), agent_state=agent_state)
    
    def ask_human_for_input(self) -> str:
        user_input = questionary.text("Enter your message:", multiline=False, qmark=">").ask(patch_stdout=True)
        return user_input 


class Server(Agent):
    @classmethod
    def from_agent_state(cls: Agent, agent_state: AgentState) -> Server:
        return cls(interface=CLIInterface(), agent_state=agent_state)
    
    def run():
        print("Hi")

def list_agents() -> List[AgentState]:
    config = MemGPTConfig.load()
    user_id = uuid.UUID(config.anon_clientid)
    ms = MetadataStore(config)
    agents = ms.list_agents(user_id)
    return agents

def process_human_input(server: Server, human_input: str):
    # first let's package up the human input
    human_message = memgpt.system.package_user_message(human_input)
    # next, let's pass this message through the memgpt system (this will internally call LLM API)

    new_messages, heartbeat_request, function_failed, token_warning, tokens_accumulated = server.step(
        human_message,
        first_message=False,
        stream=False,
    )

    skip_next_user_input = False
    user_message = human_message
    if token_warning:
        user_message = memgpt.system.get_token_limit_warning()
        skip_next_user_input = True
    elif function_failed:
        user_message = memgpt.system.get_heartbeat(FUNC_FAILED_HEARTBEAT_MESSAGE)
        skip_next_user_input = True
    elif heartbeat_request:
        user_message = memgpt.system.get_heartbeat(REQ_HEARTBEAT_MESSAGE)
        skip_next_user_input = True

    return StepResponse(new_messages, user_message, skip_next_user_input)

def greet(server_state: AgentState, conn):
    server : Server = Puppet.from_agent_state(server_state)
    while True:
        print("waiting for human to send..")
        human_input = conn.recv()
        conn.send(process_human_input(server, human_input))
    conn.close()

    
# send a fixed message from the puppet agent to the server agent 
# in our case, the message should just be a "what is your name?"



if __name__ == "__main__":
    # get all agent states
    agent_states = list_agents()
    # let's have the puppet be always the first agent, and the server the second
    puppet_state = agent_states[0]
    server_state = agent_states[-1]
    puppet = Puppet.from_agent_state(puppet_state)

    parent_conn, child_conn = mp.Pipe()

    assert len(agent_states) >= 2, "there must be at least 2 agents created already; do this via CreateAgent.py"
    # spin up a server processes
    server_process = mp.Process(target=greet, args=(server_state,child_conn,))
    server_process.start()
    while True:
        parent_conn.send(puppet.ask_human_for_input())     
        response : StepResponse = parent_conn.recv()
        response.pprint_agent_message()
    server_process.join()