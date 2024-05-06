from dataclasses import dataclass
from distributedGPT.messages.Message import Message

@dataclass
class AgentInput(Message):

    def is_valid(self):
        super().is_valid()

    @classmethod
    def from_raw(cls):
        pass