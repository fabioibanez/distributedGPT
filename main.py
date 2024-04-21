from utils.llmAPI import *

def main():
    gpt4 = gpt4Llm()
    gpt4.make_request("Compose a poem that explains the concept of recursion in programming.")
    
    
main()