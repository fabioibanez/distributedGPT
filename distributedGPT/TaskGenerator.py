
import grpc
import distributed_gpt_pb2, distributed_gpt_pb2_grpc
import random
import os
import argparse
from abc import ABC, abstractmethod
            

class TaskGenerator(ABC):
    @abstractmethod
    def get_files(self):
        pass
    @abstractmethod
    def read_files(self):
        pass
    
    @abstractmethod
    def next(self):
        pass

class DocTask(TaskGenerator):
    
    def __init__(self, document_types = []):
        self.document_types = document_types
        self.documents = self.read_files()
    
    # get_files() returns a list of filepaths 
    def get_files(self): 
        doc_dir_base = "../utils/documents/"
        # do a crawl for each doc dir
        filepaths = []
        for t in self.document_types:
            doc_dir = doc_dir_base + t
            for root, _, files in os.walk(doc_dir):
                for file in files:
                    file_splitted = file.split('.')
                    if file_splitted[-1] == 'json': continue
                    file_path = os.path.join(root, file)
                    filepaths.append(file_path)
        return filepaths

    def read_files(self):
        files = self.get_files()
        documents = dict()
        for f in files:
            handle = open(f, 'r')
            documents[f] = handle.read()
            handle.close()
        return documents
    
    def next(self):
        document_keys = list(self.documents.keys())
        sampled_document_keys = random.sample(document_keys, 1)
        documents = dict()

        for k in sampled_document_keys:
            documents[k] = self.documents[k]

        return documents


class HumanClient:
    def __init__(self, ip: str, port: int, task_generator: TaskGenerator):
        self.task_gen = task_generator
        self.ip   = ip
        self.port = port
        self.conn_addr = self.ip + ":" + str(self.port)
    
    def submit_job(self):
        documents  = self.task_gen.next()

        with grpc.insecure_channel(self.conn_addr) as channel:
            stub = distributed_gpt_pb2_grpc.LeaderStub(channel)
            document_strings = {i : documents[k] for i, k in enumerate(documents)}
            job_request : distributed_gpt_pb2.JobRequest = distributed_gpt_pb2.JobRequest(content="0", files=document_strings) 
            result = stub.submitJob(job_request) 
            print(result)


def stringify_files(path):
    with open(path, 'r') as file:
        return file.read()

if __name__ == "__main__":
    
    doctask = DocTask(['csv'])

    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", required=False, type=str, default='localhost')
    parser.add_argument("--port", required=False, type=int, default=50051)
    args = parser.parse_args()

    human = HumanClient(args.ip, args.port, doctask)
    human.submit_job()
