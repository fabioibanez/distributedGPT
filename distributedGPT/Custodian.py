from __future__ import annotations
from typing import Annotated, List, Tuple, Dict, Any, Union
from memgpt.agent import Agent, AgentState
from memgpt.config import MemGPTConfig
from memgpt.metadata import MetadataStore
from memgpt.data_types import Message, Preset
from memgpt.presets.utils import load_yaml_file
from memgpt.functions.functions import load_all_function_sets
from memgpt.presets.presets import generate_functions_json
from memgpt.interface import AgentInterface
import memgpt.system
import multiprocessing as mp
from multiprocessing.connection import Connection
from dataclasses import dataclass
from memgpt.prompts import gpt_system
from memgpt.utils import get_local_time, get_human_text, get_persona_text
from memgpt.constants import \
    JSON_ENSURE_ASCII, FUNC_FAILED_HEARTBEAT_MESSAGE, REQ_HEARTBEAT_MESSAGE, MEMGPT_DIR, \
    DEFAULT_PERSONA, DEFAULT_HUMAN

import uuid
import json


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
    def init(cls, config_dict = None) -> MultiAgentCustodian:
        if cls._custodian is None:
            cls._custodian = super().__new__(cls)

        if config_dict is None:
            config = MemGPTConfig.load()
        else:
            config = MemGPTConfig(**config_dict)
        
        cls._custodian.state = MultiAgentCustodian.CustodianKnowledge(config, MetadataStore(config))
        return cls
    
    @staticmethod
    def list_multi_agents():
        """lists all agents in the system that are following the multiagent framework"""
        assert MultiAgentCustodian._custodian is not None, "you must have initialized the Custodian class via init()"
        # access the metadata store
        ms : MetadataStore   = MultiAgentCustodian._custodian.state.metadata_store
        config: MemGPTConfig = MultiAgentCustodian._custodian.state.config
        user_id = uuid.UUID(config.anon_clientid)
        agents = ms.list_agents_having_preset(user_id, config.preset)
        return agents
    
    @staticmethod
    def delete_multi_agents():
        """deletes all agents in the system that are following the multiagent framework"""
        assert MultiAgentCustodian._custodian is not None, "you must have initialized the Custodian class via init()"
        # access the metadata store
        ms : MetadataStore   = MultiAgentCustodian._custodian.state.metadata_store
        config: MemGPTConfig = MultiAgentCustodian._custodian.state.config
        user_id = uuid.UUID(config.anon_clientid)
        ms.delete_agents_having_preset(user_id, config.preset)
    
    @staticmethod
    def create_multi_agents(N: int):
        """creates N agents in the system that follow the multiagent framework"""
        assert MultiAgentCustodian._custodian is not None, "you must have initialized the Custodian class via init()"
        # access teh metadata store
        ms : MetadataStore = MultiAgentCustodian._custodian.state.metadata_store
        config: MemGPTConfig = MultiAgentCustodian._custodian.state.config
        user_id = uuid.UUID(config.anon_clientid)
        raise NotImplementedError
        
    
    @staticmethod
    def update_multi_system_preset() -> None:
        """ updates the system prompt field of the preset used in the multiagent framework"""
        assert MultiAgentCustodian._custodian is not None, "you must have initialized the Custodian class via init()"
        ms : MetadataStore = MultiAgentCustodian._custodian.state.metadata_store
        config: MemGPTConfig = MultiAgentCustodian._custodian.state.config
        user_id = uuid.UUID(config.anon_clientid)

        filename = f"{MEMGPT_DIR}/presets/memgpt_multiagent.yaml" 
        preset_config = load_yaml_file(filename)
        preset_system_prompt = preset_config["system_prompt"]
        preset_function_set_names = preset_config["functions"]
        functions_schema = generate_functions_json(preset_function_set_names)

        updated_preset = Preset(
            user_id=user_id,
            name="memgpt_multiagent",
            system=gpt_system.get_system_text(preset_system_prompt),
            persona=get_persona_text(DEFAULT_PERSONA),
            human=get_human_text(DEFAULT_HUMAN),
            persona_name=DEFAULT_PERSONA,
            human_name=DEFAULT_HUMAN,
            functions_schema=functions_schema,
        )
        ms.update_preset(name = config.preset, user_id = user_id, changes = vars(updated_preset))
        
    @staticmethod 
    def update_agent_persona(agent_id: uuid.UUID, new_persona: str) -> None:
        """updates the persona of the agent referenced by `agent_id` to be `new_persona`"""
        assert MultiAgentCustodian._custodian is not None, "you must have initialized the Custodian class via init()"
        ms : MetadataStore = MultiAgentCustodian._custodian.state.metadata_store
        ms.update_agent_multi(agent_id, {"persona": new_persona}) 
    
    @staticmethod
    def reset_messages() -> None:
        """cleans all the messages across all agent states"""
        assert MultiAgentCustodian._custodian is not None, "you must have initialized the Custodian class via init()"
        agents = MultiAgentCustodian.list_multi_agents()
        ms : MetadataStore = MultiAgentCustodian._custodian.state.metadata_store 
        for agent in agents:
            ms.update_agent_multi(agent.id, {"state": {"messages": []}})
        
        
if __name__ == "__main__":
    custodian = MultiAgentCustodian
    custodian.init()
    agents = custodian.list_multi_agents()
    brad_persona = get_persona_text("brad")
    # let's modify the first agent's persona
    # custodian.update_agent_persona(agents[0].id, brad_persona)
    # custodian.reset_messages()
    custodian.delete_multi_agents()