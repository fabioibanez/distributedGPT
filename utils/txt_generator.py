import os
import random
from document_generators import documentGenerator, documentPrompt
from llmAPI import *
from dataclasses import dataclass
import json as JSON

DISCIPLINES = ["Accounting", "Computer Science", "Software Engineering", "Law", "Political Science", "Customer Service"]

def get_discipline():
    return random.choice(DISCIPLINES)

class txtDocumentGenerator(documentGenerator):
    '''
    Usually the SYSTEM_PERSONA would be passed in as a parameter upon construction
    and set in the parent class, documentGenerator but in this case we want our SYSTEM_PERSONA 
    to be dynamic based on discplines. in order to do this we need to set the SYSTEM_PERSONA in 
    the constructor of the child class, txtDocumentGenerator.
    '''
    def __init__(self) -> None:
        self.discipline = get_discipline()
        self.system_persona = \
        f"""You are a document generator that specialzies in txt files containting information about {self.discipline}. 
        These documents don't have any particular purpose except to just contain information about {self.discipline}.
        Do not feel limited by the constraints of a specific purpose. Just generate a document that contains information
        about {self.discipline}. The user will prompt you with a json with the following scheme: 
        revealing_context: str, pre_hash: float\.
        
        When generating a document, you must include the value referenced by the 'pre_hash' key in the document. Furthermore,
        you must include in the document the 'revealing_context' string so that a user can understand what they're looking
        for. 
        
        It is particularly likely that the revealing context provided will implicilty require you to generate a python file that
        has a particular structure or specific elements. Adhere to this while creating the document. However, the document should
        be of arbitrarity length and complexity, but it should tend to be longer. The only strong requirements are that the pre_hash
        value and the revealing_context string are included in the document. They should also be placed arbitrarily in the document with
        no particular order or structure. The revealing context should be included, but there should be no indication that the reavealing
        context is in fact a revealing context. The revealing context will usually provide a spatial indication of where the pre_hash value
        is in the document.
        
        So for example, if the revealing context is 'The value is in the second paragraph', there shouldn't be a line before that that says
        the next line contains the revealing context. The revealing context should be included in the document in a way that it is not
        immediately obvious that it is the revealing context.
        """
        super().__init__(self.system_persona)
        
    @dataclass
    class txtDocumentPrompt(documentPrompt):
        def jsonify(self):
            return vars(self)

        def stringify(self):
            json = self.jsonify()
            return JSON.dumps(json)

    def generate_document(self, txt_document_prompt_class: txtDocumentPrompt):
        document_prompt = txt_document_prompt_class.stringify()
        response = self.llm.make_request(document_prompt, self.system_persona).content

        filename = f"documents/txt/generated_document_{txt_document_prompt_class.__class__.__name__}.txt"
        counter = 1
        while os.path.exists(filename):
            filename = f"documents/txt/generated_document_{txt_document_prompt_class.__class__.__name__}_{counter}.txt"
            counter += 1

        with open(filename, "w") as file:
            file.write(response)

        return response

if __name__ == "__main__":
    generator = txtDocumentGenerator()
    pre_hash = 12
    revealing_context = "The pre_hash value is in the second sentence"
    prompt = txtDocumentGenerator.txtDocumentPrompt(pre_hash, revealing_context)
    print(generator.generate_document(prompt))