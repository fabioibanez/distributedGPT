from document_generators import documentPrompt, documentGenerator
from dataclasses import dataclass
import json as JSON
import os

SYSTEM_PERSONA = \
    """
    You are a document generator that specializes in generating CSV files of arbitrary purposes.
    These CSV files could be for instance: cost metrics of a financial firm, a simple database
    storage, even the results of a massive survey! Do not feel limited to the examples listed;
    the file contents can be of anything as long as it conforms to the scheme of an XML file.
    The user will prompt you with just a JSON having the following scheme: 
    \{revealing_context\: string, pre_hash: float\}. When generating a document you must include the
    value referenced by the key `pre_hash` somewhere in the document. 
    
    Concretely, you must write the string referenced by the key `revealing_context` in some header or 
    row of the CSV file. For example, if the pre-hash is 16 and the revealing_context is 
    'the 4th row and 4th column contain the pre-hash value', one generated CSV file could look like:
    
    h1,h2,h3,the 4th row and 4th column contain the pre-hash value
    0,0,0,0
    0,0,0,0
    0,0,0,0
    0,0,0,16
    
    
    It is likely that the inputted revealing context implicitly requires the CSV file to possess
    certain elements and/or structure. Adhere to this constraint when generating a document. However,
    pleaes feel free to generate a file of arbitrary length. Basically, both the inputted pre-hash and the revealing
    context should be embedded in a file where there are many things going on. They should be placed somewhat
    arbitrarily.
    
    In your response, provide just the CSV content. Do not add any miscellaneous text. Furthermore,
    there is no need to format anything with 3 backticks, just output the raw content with the revealing context
    and the pre-hash value somewhere in the content.
    """

class csvDocumentGenerator(documentGenerator):
    @dataclass
    class csvDocumentPrompt(documentPrompt):
        def jsonify(self) -> dict:
            return vars(self)
        
        def stringify(self) -> str:
            json = self.jsonify()
            return JSON.dumps(json)
    
    def generate_document(self, document_prompt_class: csvDocumentPrompt):
        prompt_stringified = document_prompt_class.stringify()
        response = self.llm.make_request(prompt_stringified, self.system_persona, model="gpt-4").content
        filename = f"documents/csv/generated_document_{document_prompt_class.__class__.__name__}.csv"
        counter  = 1
        while os.path.exists(filename):
            filename = f"documents/csv/generated_document_{document_prompt_class.__class__.__name__}_{counter}.csv"
            counter += 1
        
        with open(filename, "w") as file:
            file.write(response)
            
        return response

if __name__ == "__main__":
    generator = csvDocumentGenerator(SYSTEM_PERSONA)
    revealing_context = """the 5th row and 5th column contain the pre-hash value"""
    prompt = csvDocumentGenerator.csvDocumentPrompt(58, revealing_context)
    print(generator.generate_document(prompt))