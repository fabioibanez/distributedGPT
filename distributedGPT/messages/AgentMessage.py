from messages import Message
from dataclasses import dataclass

@dataclass
class AgentMessage(Message):
    src_id: int
    dst_id: int
    content: str 