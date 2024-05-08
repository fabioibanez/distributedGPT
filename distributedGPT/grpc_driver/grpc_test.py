import sys
from grpc_server import DistributedGPTLeader
from PoolInterface import PoolRPCInterface


if __name__ == '__main__':
    poolrpcInterface = PoolRPCInterface(1)
    rpc = DistributedGPTLeader(poolrpcInterface)
    rpc.serve()
    poolrpcInterface.test()
    