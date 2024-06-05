from enum import Enum
from termcolor import colored


class Logging(Enum):
    INFO      = "light_grey"   # use to emit monologues
    IMPORTANT = "light_yellow" # use to emit very important information that human should see
    DATA      = "green"        # use to emit data that's flowing through the system

def log(s: str, color: Logging, attrs = []):
    print()
    print(colored(s, color, attrs=attrs)) 
    print()

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
    
    
LEADER_TO_WORKER_PROLOGUE = \
    """
    Here you have a file that you are specialized in analyzing. Please find the unhashed value that is encoded in this
    document and apply your hash function to the value and return the hashed value. ONLY RETURN THE HASHED VALUE BASED 
    ON YOUR HASH FUNCTION IN YOUR PERSONA, AND NOTHING ELSE. Do not respond with any commentary, your answer should
    simply be the hashed value. YOU MUST call the send_message_remote function as part of your response.
    
    START OF DOCUMENT: 
    
    """