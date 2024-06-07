
import grpc
import distributed_gpt_pb2_grpc
import distributed_gpt_pb2 as proto
import json as JSON
import random
import time
import os
import argparse
from abc import ABC, abstractmethod

def PY_FUNCTION(x):
    return x + 13
def CSV_FUNCTION(x):
    return x + 69
def XML_FUNCTION(x):
    return x + 78

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
    
    def __init__(self, document_types = [], n_samples_in_batch=1):
        self.document_types = document_types
        self.n_samples_in_batch = n_samples_in_batch
        self.documents = self.read_files()
    
    # get_files() returns a list of filepaths 
    def get_files(self): 
        doc_dir_base = "/home/mnath/programming/distributedGPT/utils/documents/"
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
        sampled_document_keys = random.sample(document_keys, self.n_samples_in_batch)
        documents = dict()

        for k in sampled_document_keys:
            documents[k] = self.documents[k]

        self.documents = documents

        return documents
    
    def evaluate(self, answers):
        correct = 0
        total = len(answers)
        
        scores_categories = {'py': [0, 0], 'xml': [0,0], 'csv': [0,0]}
        for i, k in enumerate(answers):
            filepath = k
            fpath_splitted = filepath.split(".")
            extension = fpath_splitted[-1]
            
            csp_doc_json_path = "".join(fpath_splitted[:-1] + ['.json'])
            with open(csp_doc_json_path, 'r') as j:
                csp_doc_json = JSON.load(j)
                
            pred_answer = answers[k]
            prehash = csp_doc_json['pre_hash']
            scores_categories[extension][1] += 1

            try:    pred_answer = float(pred_answer)
            except: 
                print('skipping prediction ', pred_answer)
                continue

            if extension == 'py':
                true_answer = PY_FUNCTION(prehash)
            elif extension == 'xml':
                true_answer = XML_FUNCTION(prehash)
            elif extension == 'csv':
                true_answer = CSV_FUNCTION(prehash)
            else:
                raise NotImplementedError
            print(f"AGENT PREDICTED: {pred_answer} | TRUE ANSWER: {true_answer}")
            is_correct = int(true_answer == pred_answer)
            correct += is_correct
            scores_categories[extension][0] += is_correct

        print(scores_categories)


class HumanClient:
    def __init__(self, ip: str, port: int, task_generator: TaskGenerator):
        self.task_gen = task_generator
        self.ip   = ip
        self.port = port
        self.conn_addr = self.ip + ":" + str(self.port)
        self.documents = None
        self.document_mappings = {}
    
    def submit_job(self) -> int:
        documents = self.task_gen.next()
        channel = grpc.insecure_channel(self.conn_addr)
        stub = distributed_gpt_pb2_grpc.LeaderStub(channel)
        self.documents = dict()
        self.document_mappings = dict()
        for i, k in enumerate(documents):
            self.documents[i] = documents[k] 
            self.document_mappings[i] = k
        job_request = proto.JobRequest(content="0", files=self.documents) 
        result : proto.JobResponse = stub.submitJob(job_request) 
        channel.close()
        return result.ticket
    
    def get_current_document_batch(self): 
        return self.documents
    
    def get_results_for_job(self, job_id: int):
        channel = grpc.insecure_channel(self.conn_addr)
        stub = distributed_gpt_pb2_grpc.LeaderStub(channel)
        completion_request = proto.JobCompletionRequest(ticket=job_id) 
        result : proto.JobResponse = stub.getJob(completion_request)
        channel.close()
        return result
        
    def get_accuracy(self, answers):
        _answers = dict()
        for k in answers:
            fpath = self.document_mappings[k]
            _answers[fpath] = answers[k].hashed_number
            
        self.task_gen.evaluate(_answers)


def stringify_files(path):
    with open(path, 'r') as file:
        return file.read()

if __name__ == "__main__":
    
    # doctask = DocTask(["xml", "py", 'csv'])
    doctask = DocTask(['xml'], n_samples_in_batch=1)

    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", required=False, type=str, default='localhost')
    parser.add_argument("--port", required=False, type=int, default=50051)
    args = parser.parse_args()

    human = HumanClient(args.ip, args.port, doctask)
    ticket = human.submit_job()
    while True:
        time.sleep(0.5)
        print("going to get the results for job", ticket, "now!")
        results = human.get_results_for_job(ticket)
        if results.status == 0:
            print("not done yet...")
        if results.status == 1:
            print('job is done!')
            human.get_accuracy(results.response)
            break