from dataclasses import dataclass
import json
from typing import Any, Dict

from .types import MessageType


@dataclass
class NetworkMessage:
    type: MessageType
    payload: Dict[str, Any]
    signature: str = ""

    def to_json(self) -> str:
        data = {"type": self.type.value, "payload": self.payload, "signature": self.signature}
        return json.dumps(data, sort_keys=True)

    @staticmethod
    def from_json(json_str: str) -> "NetworkMessage":
        data = json.loads(json_str)
        message_type = MessageType(data["type"])
        payload = data.get("payload", {})
        signature = data.get("signature", "")
        return NetworkMessage(type=message_type, payload=payload, signature=signature)
