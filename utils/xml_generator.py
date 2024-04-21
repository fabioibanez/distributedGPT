from document_generators import documentPrompt, documentGenerator
from dataclasses import dataclass

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
    """


class xmlDocumentGenerator(documentGenerator):
    @dataclass
    class xmlDocumentPrompt(documentPrompt): pass
    
    def generate_document(self, document_prompt_class: documentPrompt):
        print(document_prompt_class)


if __name__ == "__main__":
    generator = xmlDocumentGenerator(SYSTEM_PERSONA)
    generator.generate_document()