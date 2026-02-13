from enum import Enum


class MessageType(Enum):
    HANDSHAKE = "handshake"
    TRANSACTION = "transaction"
    BLOCK = "block"
    GET_BLOCKS = "get_blocks"
    BLOCKS_RESPONSE = "blocks_response"
    PEER_LIST = "peer_list"
    PING = "ping"
    PONG = "pong"


class PeerState(Enum):
    CONNECTING = "connecting"
    HANDSHAKE = "handshake"
    READY = "ready"
    DISCONNECTED = "disconnected"
