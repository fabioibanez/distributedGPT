from PoolInterface import AgentInterface
from memgpt.data_types import AgentState
from typing import Tuple, Any

import grpc
import distributed_gpt_pb2_grpc
import distributed_gpt_pb2 as proto
from rpc_utils.parsing import parse_assignment, parse_message 
from messages import Message

from d_utils.constants import *
import json as JSON

Status = dict


class RPCAgentInterface(AgentInterface):
        
    def __init__(self, addr:str, port: int):
        # let's set up the rpc
        self.port = port
        self.addr = addr
        self.conn_addr = f"{addr}:{port}"
        
        # this will frequently update to have the current job/doc that the worker is dealing with
        self.job_id = None
        self.doc_id = None
        
    def init(self) -> Tuple[int, AgentState]:
        with grpc.insecure_channel(self.conn_addr) as channel:
            stub = distributed_gpt_pb2_grpc.LeaderStub(channel)
            assignment_request = proto.AssignmentRequest(id="0")
            result : proto.Assignment = stub.giveAgentAssignment(assignment_request)
            process_id, agent_state = parse_assignment(result)
            self.process_id = process_id
            log(f"My Process ID is {self.process_id}", Logging.IMPORTANT.value)
            return process_id, agent_state

    
    def user_message(self, msg: str, msg_obj: Message | None = None):
        pass
    
    def internal_monologue(self, msg: str, msg_obj: Message | None = None):
        log(msg, Logging.INFO.value)
    
    def assistant_message(self, msg: str, msg_obj: Message | None = None):
        print("Sending data to leader")
        print("Sent")

    def function_message(self, msg: str, msg_obj: Message | None = None):
        pass

    def close(self):
        # nothing to close on client's end
        pass
    
    ##### RPCAgentInterface specific methods #####
    
    def get_message(self) -> Any:
        """Wait for the main process to send a message, and process it"""
        with grpc.insecure_channel(self.conn_addr) as channel:
            stub = distributed_gpt_pb2_grpc.LeaderStub(channel)
            task_request = proto.TaskRequest(id=self.process_id)
            result : proto.Task = stub.giveAgentMessage(task_request)
            message = parse_message(result)
            # update the job and doc id, will be transmitted in the subsequent write_message() call
            self.job_id = message['job_id']
            self.doc_id = message['doc_id']
            return message
        
    def write_message(self, msg) -> None:
        log(f"Sending the following message to the leader", Logging.IMPORTANT.value)
        log(JSON.dumps(msg, indent=1), Logging.DATA.value)
        
        with grpc.insecure_channel(self.conn_addr) as channel:
            stub = distributed_gpt_pb2_grpc.LeaderStub(channel)
            agent_message = proto.LeaderToWorkerMessage(**msg, doc_id=self.doc_id, job_id=self.job_id)
            result : proto.Status = stub.processAgentMessage(agent_message)
            return result
        
    def say_goodbye(self):
        with grpc.insecure_channel(self.conn_addr) as channel:
            stub = distributed_gpt_pb2_grpc.LeaderStub(channel)
            goodbye_message = proto.GoodbyeMessage(id = self.process_id)
            result : proto.Status = stub.sayGoodbye(goodbye_message)
