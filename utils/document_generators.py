from abc import ABC, abstractmethod
from llmAPI import *
from dataclasses import dataclass
from sys import stdin

@dataclass
class documentPrompt:
    pre_hash: float
    revealing_context: str
    system_persona: str
    def transform_to_string(self):
        return "value=" + str(self.pre_hash) + " revealing context=" + self.revealing_context


class documentGenerator(ABC):
    def __init__(self) -> None:
        self.llm = gpt4Llm()


    @abstractmethod
    def generate_document(self, document_prompt_class: documentPrompt):
        '''
        Transform documentPrompt struct into a string
        '''
        raise NotImplementedError
    
    
class pythonDocumentGenerator(documentGenerator):
    @dataclass
    class pythonDocumentPrompt(documentPrompt):
        system_persona: str = "I am a document generator that specializes in generating \
            Python programs. I will generate a non-trivial Python program that contains within it \
            a hash value that is equal to the pre_hash value. The program will also contain a revealing context \
            that will help a GPT model to predict the pre_hash value."
    
    
    def generate_document(self, python_document_prompt_class: pythonDocumentPrompt):
        document_prompt = python_document_prompt_class.transform_to_string()
        
        result = self.llm.make_request(document_prompt, python_document_prompt_class.system_persona)
        filename = f"documents/py/generated_document_{python_document_prompt_class.__class__.__name__}.py"
        counter = 1
        
        while os.path.exists(filename):
            filename = f"documents/py/generated_document_{python_document_prompt_class.__class__.__name__}_{counter}.py"
            counter += 1
            
        with open(filename, "w") as file:
            file.write(result)
            
        # return result for purposes of testing
        return result
        
    
        
if __name__ == "__main__":
    python_document_generator = pythonDocumentGenerator()
    python_document_generator.generate_document(pythonDocumentGenerator.pythonDocumentPrompt(0.5, "The value you are looking for is less than 1 but greater than 0"))