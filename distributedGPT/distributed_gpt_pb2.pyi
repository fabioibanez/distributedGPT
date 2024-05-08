from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AssignmentRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class LLMConfig(_message.Message):
    __slots__ = ("model", "model_endpoint_type", "model_endpoint", "model_wrapper", "context_window")
    MODEL_FIELD_NUMBER: _ClassVar[int]
    MODEL_ENDPOINT_TYPE_FIELD_NUMBER: _ClassVar[int]
    MODEL_ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    MODEL_WRAPPER_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_WINDOW_FIELD_NUMBER: _ClassVar[int]
    model: str
    model_endpoint_type: str
    model_endpoint: str
    model_wrapper: str
    context_window: int
    def __init__(self, model: _Optional[str] = ..., model_endpoint_type: _Optional[str] = ..., model_endpoint: _Optional[str] = ..., model_wrapper: _Optional[str] = ..., context_window: _Optional[int] = ...) -> None: ...

class EmbeddingConfig(_message.Message):
    __slots__ = ("embedding_endpoint_type", "embedding_endpoint", "embedding_model", "embedding_dim", "embedding_chunk_size")
    EMBEDDING_ENDPOINT_TYPE_FIELD_NUMBER: _ClassVar[int]
    EMBEDDING_ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    EMBEDDING_MODEL_FIELD_NUMBER: _ClassVar[int]
    EMBEDDING_DIM_FIELD_NUMBER: _ClassVar[int]
    EMBEDDING_CHUNK_SIZE_FIELD_NUMBER: _ClassVar[int]
    embedding_endpoint_type: str
    embedding_endpoint: str
    embedding_model: str
    embedding_dim: int
    embedding_chunk_size: int
    def __init__(self, embedding_endpoint_type: _Optional[str] = ..., embedding_endpoint: _Optional[str] = ..., embedding_model: _Optional[str] = ..., embedding_dim: _Optional[int] = ..., embedding_chunk_size: _Optional[int] = ...) -> None: ...

class PropertyDescription(_message.Message):
    __slots__ = ("type", "description")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    type: str
    description: str
    def __init__(self, type: _Optional[str] = ..., description: _Optional[str] = ...) -> None: ...

class Parameters(_message.Message):
    __slots__ = ("type", "properties", "required")
    class PropertiesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: PropertyDescription
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[PropertyDescription, _Mapping]] = ...) -> None: ...
    TYPE_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    REQUIRED_FIELD_NUMBER: _ClassVar[int]
    type: str
    properties: _containers.MessageMap[str, PropertyDescription]
    required: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, type: _Optional[str] = ..., properties: _Optional[_Mapping[str, PropertyDescription]] = ..., required: _Optional[_Iterable[str]] = ...) -> None: ...

class Function(_message.Message):
    __slots__ = ("name", "description", "parameters")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    name: str
    description: str
    parameters: Parameters
    def __init__(self, name: _Optional[str] = ..., description: _Optional[str] = ..., parameters: _Optional[_Union[Parameters, _Mapping]] = ...) -> None: ...

class State(_message.Message):
    __slots__ = ("persona", "human", "system", "functions", "messages")
    PERSONA_FIELD_NUMBER: _ClassVar[int]
    HUMAN_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_FIELD_NUMBER: _ClassVar[int]
    FUNCTIONS_FIELD_NUMBER: _ClassVar[int]
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    persona: str
    human: str
    system: str
    functions: _containers.RepeatedCompositeFieldContainer[Function]
    messages: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, persona: _Optional[str] = ..., human: _Optional[str] = ..., system: _Optional[str] = ..., functions: _Optional[_Iterable[_Union[Function, _Mapping]]] = ..., messages: _Optional[_Iterable[str]] = ...) -> None: ...

class AgentState(_message.Message):
    __slots__ = ("name", "user_id", "persona", "human", "llm_config", "embedding_config", "preset", "id", "state")
    NAME_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    PERSONA_FIELD_NUMBER: _ClassVar[int]
    HUMAN_FIELD_NUMBER: _ClassVar[int]
    LLM_CONFIG_FIELD_NUMBER: _ClassVar[int]
    EMBEDDING_CONFIG_FIELD_NUMBER: _ClassVar[int]
    PRESET_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    name: str
    user_id: str
    persona: str
    human: str
    llm_config: LLMConfig
    embedding_config: EmbeddingConfig
    preset: str
    id: str
    state: State
    def __init__(self, name: _Optional[str] = ..., user_id: _Optional[str] = ..., persona: _Optional[str] = ..., human: _Optional[str] = ..., llm_config: _Optional[_Union[LLMConfig, _Mapping]] = ..., embedding_config: _Optional[_Union[EmbeddingConfig, _Mapping]] = ..., preset: _Optional[str] = ..., id: _Optional[str] = ..., state: _Optional[_Union[State, _Mapping]] = ...) -> None: ...

class Assignment(_message.Message):
    __slots__ = ("process_id", "agent_state")
    PROCESS_ID_FIELD_NUMBER: _ClassVar[int]
    AGENT_STATE_FIELD_NUMBER: _ClassVar[int]
    process_id: int
    agent_state: AgentState
    def __init__(self, process_id: _Optional[int] = ..., agent_state: _Optional[_Union[AgentState, _Mapping]] = ...) -> None: ...
