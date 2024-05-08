import distributedGPT_pb2
import distributedGPT_pb2_grpc
import time
import grpc
import json

class DistributedGPTClient:
    def __init__(self, client_id, channel : str):
        self.client_id = client_id
        self.channel = grpc.insecure_channel(channel)
        self.stub = distributedGPT_pb2_grpc.NodeServiceStub(self.channel)

    def send_message_to_leader(self, message):
        """
        The main purpose of this method is to send a message to the leader
        like requesting to communicate with another client, etc.
        """
        json_message = json.dumps(message)
        request = distributedGPT_pb2.ClientMessage(client_id=self.client_id, message=json_message)
        response = self.stub.SendMessageToLeader(request)
        print("The leader responded with:", response.message)
        return json.loads(response.message)
       
      
    def receive_message_from_leader(self):
        """
        Receives messages from the leader
        """
        for message in self.stub.SendMessageToClient(distributedGPT_pb2.LeaderMessage()):
            print("Received message from leader:", message.message)  
        
    def register_client(self):
        """
        registers a client with leaderGPT
        """
        request = distributedGPT_pb2.RegisterClientRequest(client_id=self.client_id)
        response = self.stub.RegisterClient(request)
        print("Client registration response:", response.message)
        return json.loads(response.message)


class FrontEndDistributedGPTClient:
    def __init__(self, client_id, channel : str):
        # should have a special client_id
        self.client_id = client_id
        self.channel = grpc.insecure_channel(channel)
        self.stub = distributedGPT_pb2_grpc.NodeServiceStub(self.channel) 
        
    def submit_job(self, job: str):
        request = distributedGPT_pb2.JobRequest(id=0, description=job)
        response = self.stub.handleSubmitJob(request)
        return response



if __name__ == '__main__':
    client_id = "1"
    run_client(client_id)