import sys
sys.path.append('/home/fabioi/distributedGPT')
from grpc_server import DistributedGPTLeader
from distributedGPT.PoolInterface import PoolRPCInterface


if __name__ == '__main__':
    poolrpcInterface = PoolRPCInterface(1)
    rpc = DistributedGPTLeader(poolrpcInterface)
    rpc.serve()
    poolrpcInterface.test()
    