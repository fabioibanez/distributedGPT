from AgentPool import *
from PoolInterface import *
from ProcessAgent import *
from AgentInterface import *


def main():
    num_agents = 1
    AgentPool(num_agents, InterfaceTypes.PIPE)
    
main()