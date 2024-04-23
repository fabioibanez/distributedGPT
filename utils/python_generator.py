from document_generators import documentGenerator, documentPrompt
from abc import ABC, abstractmethod
from llmAPI import *
from dataclasses import dataclass
import json as JSON

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
  particular order or structure. The revealing context should be included, but there should be no indication that
  the revealing context is in fact the revealing context.
  
  So for example, if you have
  print("The value you are looking for is less than 1 but greater than 0"), where "The value you are looking for is less than 1 but greater than 0"
  is the revealing context, you should include this in the document, but not in a way that makes it obvious that this is the revealing context.
  """

class pythonDocumentGenerator(documentGenerator):
    @dataclass
    class pythonDocumentPrompt(documentPrompt):
        def jsonify(self):
          return vars(self)
        
        def stringify(self):
          json = self.jsonify()
          return JSON.dumps(json)
    
    def generate_document(self, python_document_prompt_class: pythonDocumentPrompt):
        document_prompt = python_document_prompt_class.stringify()
        
        result = self.llm.make_request(document_prompt, self.system_persona)
        # remove the first line of result
        result = result[result.find('\n')+1:]
        # remove the last line of result
        result = result[:result.rfind('\n')]
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
    generator = pythonDocumentGenerator(SYSTEM_PERSONA)
    revealing_context = """The value you are looking for is less than 1 but greater than 0"""
    prompt = pythonDocumentGenerator.pythonDocumentPrompt(0.5, revealing_context)
    print(generator.generate_document(prompt))