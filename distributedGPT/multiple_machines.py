# TODO add gRPC driver code here
import argparse
from AgentPool import AgentPool, InterfaceTypes
from ProcessAgent import ProcessAgent
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", required=True, type=str, choices=['client', 'server'])
    args = parser.parse_args()
    if args.type == "client":
        # spin up a client
        agent = ProcessAgent.as_rpc_client(port=50051)
        ProcessAgent.event_loop(agent)
    else:
        # spin up a server
        AgentPool(2, InterfaceTypes.RPC)