from distributed_gpt_pb2 import Assignment, Task
from memgpt.data_types import AgentState, LLMConfig, EmbeddingConfig
from typing import Tuple
from uuid import UUID
from google.protobuf.json_format import MessageToDict

def parse_assignment(assignment: Assignment) -> Tuple[int, AgentState]:
    process_id  = assignment.process_id
    agent_state = MessageToDict(assignment.agent_state, preserving_proto_field_name=True)
    agent_state['user_id'] = UUID(agent_state['user_id'])
    agent_state['id'] = UUID(agent_state['id'])
    agent_state['llm_config'] = LLMConfig(**agent_state['llm_config'])
    agent_state['embedding_config'] = EmbeddingConfig(**agent_state['embedding_config'])
    return process_id, AgentState(**agent_state)
    
def parse_message(task: Task) -> dict:
    message = MessageToDict(task, preserving_proto_field_name=True)
    return message