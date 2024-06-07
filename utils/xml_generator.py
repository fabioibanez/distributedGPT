from document_generators import documentPrompt, documentGenerator
import random
from dataclasses import dataclass
import string
import json as JSON
import os

SYSTEM_PERSONA = \
    """
    You are a document generator that specializes in generating XML files of arbitrary purposes.
    These XML files could be for instance: configuration details of a service, a simple key-value
    storage, even the model file of a MuJoCo scene! Do not feel limited to the examples listed;
    the file contents can be of anything as long as it conforms to the scheme of an XML file.
    The user will prompt you with just a JSON having the following scheme: 
    \{revealing_context\: string, pre_hash: float\}. When generating a document you must include the
    value referenced by the key `pre_hash` somewhere in the document. Furthermore, you must include
    — as an XML comment — the string referenced by the key `revealing_context` somewhere in the document.
    
    It is likely that the inputted revealing context implicitly requires the XML file to possess
    certain elements and/or structure. Adhere to this constraint when generating a document. However,
    pleaes feel free to generate a file of arbitrary length. Basically, both the inputted pre-hash and the revealing
    context should be embedded in a file where there are many things going on. They should be placed somewhat
    arbitrarily.
    """


class xmlDocumentGenerator(documentGenerator):
    @dataclass
    class xmlDocumentPrompt(documentPrompt):
        def jsonify(self) -> dict:
            return vars(self)

        def stringify(self) -> str:
            json = self.jsonify() 
            return JSON.dumps(json)
    
    def generate_document(self, document_prompt_class: xmlDocumentPrompt):
        prompt_stringified = document_prompt_class.stringify()
        response = self.llm.make_request(prompt_stringified, self.system_persona, model='gpt-4o').content
    
        # make a folder for this document 
        base = f"documents/xml/generated_document_{document_prompt_class.__class__.__name__}_0/"

        counter = 0
        while os.path.isdir(base):
            counter += 1
            base = f"documents/xml/generated_document_{document_prompt_class.__class__.__name__}_{counter}/"
            
        os.makedirs(base, exist_ok=True)

        xml_file = f"generated_document_{document_prompt_class.__class__.__name__}_{counter}.xml"
        json_file = f"generated_document_{document_prompt_class.__class__.__name__}_{counter}.json"
        
        xml_filename  = base + xml_file
        json_filename = base + json_file
            
        with open(xml_filename, "w+") as file:
            file.write(response)
        
        with open(json_filename, "w+") as file:
            JSON.dump(vars(document_prompt_class), file)
            
        return response


if __name__ == "__main__":
    generator = xmlDocumentGenerator(SYSTEM_PERSONA)
    for i in range(20):
        random_attribute = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        random_tag = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        revealing_context = f"""the {random_attribute} attribute of the <{random_tag}> tag contains the pre-hash value."""
        prehash = random.randint(0, 100)
        prompt = xmlDocumentGenerator.xmlDocumentPrompt(prehash, revealing_context)
        print(generator.generate_document(prompt))