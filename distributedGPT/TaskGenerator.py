
import grpc
import distributed_gpt_pb2, distributed_gpt_pb2_grpc
import argparse
            
def stringify_files(path):
    with open(path, 'r') as file:
        return file.read()

if __name__ == "__main__":
    document1_path = "../utils/documents/xml/test.xml"
    document2_path = "../utils/documents/py/test.py"
    document3_path = "../utils/documents/csv/test.csv"
    
    document1_string = stringify_files(document1_path)
    document2_string = stringify_files(document2_path)
    document3_string = stringify_files(document3_path)

    parser = argparse.ArgumentParser()
    parser.add_argument("--type", required=True, type=str, choices=['client', 'server'])
    parser.add_argument("--ip", required=False, type=str, default='localhost')
    parser.add_argument("--port", required=False, type=int, default=50051)
    args = parser.parse_args()
    conn_addr = args.ip + ":" + str(args.port)
    with grpc.insecure_channel(conn_addr) as channel:
        stub = distributed_gpt_pb2_grpc.LeaderStub(channel)
        assignment_request = distributed_gpt_pb2.AssignmentRequest(id="0")
        result : distributed_gpt_pb2.Assignment = stub.giveAgentAssignment(assignment_request)
        documents = {0: document1_string, 1: document2_string, 3: document3_string}
        job_request : distributed_gpt_pb2.JobRequest = distributed_gpt_pb2.JobRequest(id="0", document=documents)