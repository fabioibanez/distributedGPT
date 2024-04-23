from abc import ABC, abstractmethod
from llmAPI import *
from dataclasses import dataclass

@dataclass
class documentPrompt:
    pre_hash: float
    revealing_context: str

class documentGenerator(ABC):
    def __init__(self, system_persona) -> None:
        self.llm = gpt4Llm()
        self.system_persona = system_persona

    @abstractmethod
    def generate_document(self, document_prompt_class: documentPrompt):
        '''
        Transform documentPrompt struct into a string
        '''
        raise NotImplementedError