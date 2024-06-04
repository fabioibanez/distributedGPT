'''
 ** TODO **
1. make a default task, which is just the one we outlined in the vision document
2. set up a datastructure for the leader to keep state on all of the workers and their
   personas
3. Write code that puts files in a mode that GPT API call can parse it/interpret it
4. Get n distinct hash functions


*** The client should be able to make a gRPC call to invoke a task getting sovled ***
'''

from AgentPool import AgentPool, InterfaceTypes

DEFAULT_TASK = ""

class TaskGenerator:
    def __init__(self, num_agents: int, addr: str = "localhost", port: int = 50051) -> None:
        self.task = task
        self.num_agents = num_agents
        self.agent_pool = AgentPool(num_agents, InterfaceTypes.RPC, addr=addr, port=port)
        
    def run_task(self, task: str):
        raise NotImplementedError
    
    
if __name__ == "__main__":
    task = TaskGenerator(DEFAULT_TASK, 1)
    task.run_task()
    
    
    
    