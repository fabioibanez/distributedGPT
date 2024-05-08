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
        ProcessAgent.as_rpc_client()
    else:
        # spin up a server
        AgentPool(1, InterfaceTypes.RPC)