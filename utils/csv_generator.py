from document_generators import documentPrompt, documentGenerator
import random
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
    there is no need to format anything with 3 backticks. JUST output the raw content WITH the revealing context
    AND the pre-hash value somewhere in the content.
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
        response = self.llm.make_request(prompt_stringified, self.system_persona, model="gpt-4o").content
        
        # make a folder for this document 
        base = f"documents/csv/generated_document_{document_prompt_class.__class__.__name__}_0/"

        counter = 0
        while os.path.isdir(base):
            counter += 1
            base = f"documents/csv/generated_document_{document_prompt_class.__class__.__name__}_{counter}/"
            
        os.makedirs(base, exist_ok=True)

        csv_file = f"generated_document_{document_prompt_class.__class__.__name__}_{counter}.csv"
        json_file = f"generated_document_{document_prompt_class.__class__.__name__}_{counter}.json"
        
        csv_filename  = base + csv_file
        json_filename = base + json_file
            
        with open(csv_filename, "w+") as file:
            file.write(response)
        
        with open(json_filename, "w+") as file:
            JSON.dump(vars(document_prompt_class), file)
            
        return response

if __name__ == "__main__":
    generator = csvDocumentGenerator(SYSTEM_PERSONA)
    for i in range(5):
        random_row    = random.randint(1, 11)
        random_col    = random.randint(1, 11)
        prehash_value = random.randint(0, 100)
        revealing_context = f"""the entry at row number {random_row} and column number {random_col} contain the pre-hash value"""
        prompt = csvDocumentGenerator.csvDocumentPrompt(prehash_value, revealing_context)
        print(generator.generate_document(prompt))