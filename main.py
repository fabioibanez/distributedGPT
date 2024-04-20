from utils.llm_api import *

def main():
    gpt4 = gpt4llm()
    gpt4.make_request("Compose a poem that explains the concept of recursion in programming.")
    
    
main()