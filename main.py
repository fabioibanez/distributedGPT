from utils.llmAPI import *

def main():
    gpt4 = gpt4Llm()
    prompt = "Compose a poem that explains the concept of recursion in programming."
    persona = "I am a poet. I am going to write a poem about recursion in programming."
    print(gpt4.make_request(prompt, persona))
    

main()