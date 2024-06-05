from document_generators import documentGenerator, documentPrompt
from abc import ABC, abstractmethod
from llmAPI import *
from dataclasses import dataclass
import json as JSON
import random

SYSTEM_PERSONA = \
  """
  You are a document generator that specializes in generating python files for arbitrary tasks.
  These python files could be for instance doing mathematical calculations, generating random numbers,
  or running a recursive algorithm like serpinski's triangle! Do not feel limited by these examples,
  as you can generate any python file you'd want as long as it is valid python code. The user will prompt
  you with just a JSON having the following scheme:
  \{revealing_context: str, pre_hash: float\}. When generating a document you must include the value
  referenced by the 'pre_hash' key somewhere in the document. Furether more you must include in a comment
  or another way the 'revealing_context' string so that the user can understand what value they're looking for
  
  It is likely that the revealing context provided will implicitly require you to genereate a python file that
  has a particular structure or specific elements. Adhere to this while creating the document. However, the document
  should be of arbitrary length and complexity. The only strong requirements are that the pre_hash value and the
  revealing context are included in the document. They should also be placed arbitrarily in the document with no
  particular order or structure. THE REVEALING CONTEXT SHOULD BE INCLUDED SOMEHOW.
  
  In your response, provide just the Python content. Do not add any miscellaneous text. Furthermore,
  there is no need to format anything with 3 backticks. JUST output the raw content WITH the revealing context
  AND the pre-hash value somewhere in the content.
  """

class pythonDocumentGenerator(documentGenerator):
    @dataclass
    class pythonDocumentPrompt(documentPrompt):
        def jsonify(self):
          return vars(self)
        
        def stringify(self):
          json = self.jsonify()
          return JSON.dumps(json)
    
    def generate_document(self, document_prompt_class: pythonDocumentPrompt):
        prompt_stringified = document_prompt_class.stringify()
        response = self.llm.make_request(prompt_stringified, self.system_persona, model="gpt-4o").content
         
        base = f"documents/py/generated_document_{document_prompt_class.__class__.__name__}_0/"
        
        
        counter = 0
        while os.path.isdir(base):
            counter += 1
            base = f"documents/py/generated_document_{document_prompt_class.__class__.__name__}_{counter}/"
            
            
        os.makedirs(base, exist_ok=True)

        py_file = f"generated_document_{document_prompt_class.__class__.__name__}_{counter}.py"
        json_file = f"generated_document_{document_prompt_class.__class__.__name__}_{counter}.json"
        
        py_filename  = base + py_file
        json_filename = base + json_file
            
        with open(py_filename, "w+") as file:
            file.write(response)
        
        with open(json_filename, "w+") as file:
            JSON.dump(vars(document_prompt_class), file)

        return response
        
    
        
if __name__ == "__main__":
    generator = pythonDocumentGenerator(SYSTEM_PERSONA)
    revealing_context = """The value you are looking for is less than 1 but greater than 0"""
    for i in range(10):
      unhashed_value = random.random()
      prompt = pythonDocumentGenerator.pythonDocumentPrompt(unhashed_value, revealing_context)
      print(generator.generate_document(prompt))