#############
"""
Baseline Steps:
1. Fetch documents (via) Task Generator
2. Construct a system prompt that provides a) the hash functions and b) the instruction for applying
   the hash function(s) to the files
3. Have the GPT follow the same instructions as in the multi-agent case, where it goes ahead and
   tries to get the encoded value from the original value present in each document.
4. Output the dictionary of values and run a verification function that checks whether returned ans
   are correct.
"""
##############
import json as JSON
from TaskGenerator import DocTask 
from llmAPI import gpt4Llm


XML_ENCODE_FUNCTION = "f(x) = x + 78"
PY_ENCODE_FUNCTION  = "f(x) = x + 13"
CSV_ENCODE_FUNCTION = "f(x) = x + 69"

hash_functions = {
   "\tUSE ON XML FILES" : XML_ENCODE_FUNCTION,
   "\tUSE ON PY FILES"  : PY_ENCODE_FUNCTION,
   "\tUSE ON CSV FILES" : CSV_ENCODE_FUNCTION 
}

formatted_string = '\n'.join([f"{key}: {value}" for key, value in hash_functions.items()])

SINGLE_GPT_SYSTEM_PROMPT = \
   f"""
   There are {len(hash_functions)} that I have at my disposal. I can apply these functions on
   values that are of interest to my human user. I MUST ensure that I do not apply these functions
   in the wrong setting or to the wrong input. Below I enumerate the hash functions that I have,
   listed as a Python dictionary-like mapping from the situation the hash function should be used in, 
   to the actual mathematical description of the hash function. When a user prompts me, I must only
   respond with the output of applying my hash function to the certain value of interest. I should
   output no commentary whatsoever.
   
   BEGIN OF MAPPING FROM SITUATION TO HASH FUNCTION:
   """ + formatted_string

USER_PROMPT_PROLOGUE = \
   """
   Below is the content of a file that you shuold analyze. Please find the unhashed value that is encoded in this
   document and apply the correct hash function to the value and return the hashed value. ONLY RETURN THE HASHED VALUE, AND NOTHING ELSE. 
   Do not respond with any commentary, your answer should simply be the hashed value.
    
   START OF DOCUMENT:
   
   """

doctask = DocTask(['xml', 'py', 'csv'], n_samples_in_batch=60)
print(SINGLE_GPT_SYSTEM_PROMPT)
llm = gpt4Llm()
files = doctask.next()
answers = dict()

for f in files:
   print("answering for filename ", f)
   doc_content = files[f]
   prompt = USER_PROMPT_PROLOGUE + doc_content
   res = llm.make_request(prompt = prompt, persona = SINGLE_GPT_SYSTEM_PROMPT, model = 'gpt-4o')
   answers[f] = res.content

doctask.evaluate(answers)