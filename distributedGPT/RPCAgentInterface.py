from PoolInterface import AgentInterface
from memgpt.data_types import AgentState
from typing import Tuple, Any, List
import grpc
import distributed_gpt_pb2, distributed_gpt_pb2_grpc
from rpc_utils.parsing import parse_assignment, parse_message 
from messages import Message

Status = dict


class RPCAgentInterface(AgentInterface):
        
    def __init__(self, addr:str, port: int):
        # let's set up the rpc
        self.port = port
        self.addr = addr
        self.conn_addr = f"{addr}:{port}"
        self.job_id = 0
        
    def init(self) -> Tuple[int, AgentState]:
        with grpc.insecure_channel(self.conn_addr) as channel:
            stub = distributed_gpt_pb2_grpc.LeaderStub(channel)
            assignment_request = distributed_gpt_pb2.AssignmentRequest(id="0")
            result : distributed_gpt_pb2.Assignment = stub.giveAgentAssignment(assignment_request)
            process_id, agent_state = parse_assignment(result)
            self.process_id = process_id
            print("My Process ID is", self.process_id)
            return process_id, agent_state

    
    def user_message(self, msg: str, msg_obj: Message | None = None):
        print("Calling user_message")
    
    def internal_monologue(self, msg: str, msg_obj: Message | None = None):
        print("Calling internal_monologue")
    
    def assistant_message(self, msg: str, msg_obj: Message | None = None):
        print("Sending data to leader")
        print("Sent")

    def function_message(self, msg: str, msg_obj: Message | None = None):
        print("Calling a function!")

    def close(self):
        # nothing to close on client's end
        pass
    
    ##### RPCAgentInterface specific methods #####
    
    def get_message(self) -> Any:
        """Wait for the main process to send a message, and process it"""
        with grpc.insecure_channel(self.conn_addr) as channel:
            stub = distributed_gpt_pb2_grpc.LeaderStub(channel)
            task_request = distributed_gpt_pb2.TaskRequest(id=self.process_id)
            result : distributed_gpt_pb2.Task = stub.giveAgentMessage(task_request)
            message = parse_message(result)
            return message
        
    def write_message(self, msg) -> None:
        with grpc.insecure_channel(self.conn_addr) as channel:
            stub = distributed_gpt_pb2_grpc.LeaderStub(channel)
            agent_message = distributed_gpt_pb2.AgentMessage(**msg)
            result : distributed_gpt_pb2.Status = stub.processAgentMessage(agent_message)
            return result
        
    def say_goodbye(self):
        with grpc.insecure_channel(self.conn_addr) as channel:
            stub = distributed_gpt_pb2_grpc.LeaderStub(channel)
            goodbye_message = distributed_gpt_pb2.GoodbyeMessage(id = self.process_id)
            result : distributed_gpt_pb2.Status = stub.sayGoodbye(goodbye_message)