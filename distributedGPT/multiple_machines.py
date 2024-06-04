import argparse
from AgentPool import AgentPool, InterfaceTypes
from ProcessAgent import ProcessAgent
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", required=True, type=str, choices=['client', 'server'])
    parser.add_argument("--ip", required=False, type=str, default='localhost')
    parser.add_argument("--port", required=False, type=int, default=50051)
    args = parser.parse_args()
    if args.type == "client":
        # spin up a client
        agent = ProcessAgent.as_rpc_client(args.ip, args.port)
        ProcessAgent.event_loop(agent)
    else:
        # spin up a server
        AgentPool(3, InterfaceTypes.RPC, addr=args.ip, port=args.port)