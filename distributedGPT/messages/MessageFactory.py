from __future__ import annotations
from memgpt.data_types import Message
from dataclasses import dataclass
from memgpt.utils import get_local_time
from memgpt.constants import JSON_ENSURE_ASCII, FUNC_FAILED_HEARTBEAT_MESSAGE, REQ_HEARTBEAT_MESSAGE
import json

class MessageFactory:

    @staticmethod
    def create_agent_input(msg: Message) -> str:
        formatted_time = get_local_time()
        packaged_message = {
            "type": "user_message",
            "message": msg,
            "time": formatted_time,
        }
        return json.dumps(packaged_message, ensure_ascii=JSON_ENSURE_ASCII)