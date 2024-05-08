import grpc
import distributedGPT_pb2
import distributedGPT_pb2_grpc
from concurrent import futures
import json
from collections import deque
from dataclasses import dataclass

@dataclass
class Job:
    id: int
    description: str


class DistributedGPTLeader(distributedGPT_pb2_grpc.NodeServiceServicer):
    def __init__(self, assoc_pool):
        self.clients = {}
        self.assoc_pool = assoc_pool

    def handleSubmitJob(self, request, context):
        # the frontend submits a job to the server at this endpoint
        # the server needs to handle the job
        # who should this job be sent to?
        # store the job in some pending job queue to represent that it is in progress
        self.assoc_pool.job_queue.append(Job(id=request.id, description=request.description))
        
    def test(self):
        print("The leader is ready to receive messages!")
                 

def serve():
    print("#### Leader is listening for messages ####")
    
    
   
    # can handle max 10 concurrent RPC calls at any moment in time
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    ip_port = input("Please input an IP address and a port for the leader: ")
    listen_on = ip_port if ip_port else '[::]:50051'
    
    distributedGPT_pb2_grpc.add_NodeServiceServicer_to_server(DistributedGPTLeader(), server)
        
    server.add_insecure_port(listen_on)
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()