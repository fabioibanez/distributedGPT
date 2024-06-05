from enum import Enum

class Logging(Enum):
    INFO      = "light_grey"
    IMPORTANT = "light_yellow"

class JobStatus(Enum):
    FAIL      = -1
    PENDING   = 0
    COMPLETED = 1 

DOCUMENT_MAPPING_MESSAGE = \
    """
    Below I provide a dictionary where the key is an integer representing the ID of a persona, and 
    the value is going to be a string representing the description of that persona:
    
    %s
    
    END OF PERSONA DICTIONARY
     
    The user will prompt you with a series of documents. These documents will be contaiend in a
    Python dictionary such that the key of the dictionary is the ID of the document, and the value
    is the content of that particular document.EACH DOCUMENT PERTAINS TO A SPECIFIC PERSONA, 
    BASED ON THE CONTENT OF THE DOCUMENT. For each prompt, your job will be to construct a dictionary 
    that maps the document ID to the ID of the persona that best pertains to that document. 
    For example, a Python document should be mapped to a persona that is concerned with all things software engineering. 
    Only output this dictionary, no commentary please of any kind. The output must be raw text,
    no markdown or any special formatting.
    
    This is the end of the system instruction.
    """
