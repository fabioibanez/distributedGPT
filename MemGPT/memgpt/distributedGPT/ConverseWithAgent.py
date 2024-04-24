from typing import List
from memgpt.metadata import MetadataStore
from memgpt.agent import Agent
from memgpt.data_types import AgentState
from memgpt.constants import FUNC_FAILED_HEARTBEAT_MESSAGE, REQ_HEARTBEAT_MESSAGE
from memgpt.config import MemGPTConfig
import memgpt.system
from memgpt.streaming_interface import StreamingRefreshCLIInterface as interface  # for printing to terminal

import uuid
import questionary

def list_agents() -> List[AgentState]:
    config = MemGPTConfig.load()
    user_id = uuid.UUID(config.anon_clientid)
    ms = MetadataStore(config)
    agents = ms.list_agents(user_id)
    return agents
    
def process_agent_step(agent, user_message, no_verify):
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


def main():
    # first let's list out all the agents we currently have
    agents = list_agents()
    # let's converse with the first agent
    agent  = agents[0]
    memgpt_agent = Agent(interface=interface(), agent_state=agent)
    # get user input
    user_input = questionary.text(
        "Enter your message:", multiline=False, qmark=">"
    ).ask()
    user_message = memgpt.system.package_user_message(user_input)
    while True:
        new_messages, user_message, skip_next_user_input = process_agent_step(memgpt_agent, user_message, False)
        break
    print(new_messages)


if __name__ == "__main__":
    main()
