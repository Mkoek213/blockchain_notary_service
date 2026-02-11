from dataclasses import dataclass
from queue import Queue
from typing import Any, Dict, List, Optional

import pytest

pytest.importorskip("cryptography")

from blockchain_core.block_builder import BlockBuilder
from blockchain_core.notarial_document import Transaction, VotingResult
from network.block_adapter import block_from_dict, document_from_dict
from network.discovery import DiscoveryService
from network.message import NetworkMessage
from network.peer_manager import PeerManager
from network.synchronizer import BlockSynchronizer
from network.types import MessageType


class StubChain:
    def __init__(self) -> None:
        self.height = 1
        self.latest_hash = "hash"
        self.received_transactions: List[Dict[str, Any]] = []
        self.received_blocks: List[Any] = []
        self.block_store: List[Any] = []

    def get_height(self) -> int:
        return self.height

    def get_latest_block_hash(self) -> str:
        return self.latest_hash

    def get_blocks_from(self, height: int) -> List[Any]:
        return self.block_store[height:]

    def validate_and_add_block(self, block: Any) -> bool:
        self.received_blocks.append(block)
        return True

    def handle_transactions(self, tx_data: dict) -> None:
        self.received_transactions.append(tx_data)


@dataclass
class StubPeer:
    remote_height: int
    sent: List[NetworkMessage]
class DummyIdentityManager:
    def get_self_certificate(self) -> Any:
        return None

    def sign_data(self, data: bytes) -> bytes:
        return b""

    def validate_peer(self, cert: Any) -> bool:
        return False

    def verify_peer_signature(self, data: bytes, signature: bytes, cert: Any) -> bool:
        return False


    def send(self, msg: NetworkMessage) -> None:
        self.sent.append(msg)


def build_block_dict() -> Dict[str, Any]:
    builder = BlockBuilder()
    builder.set_parent_hash("parent")
    builder.set_author("miner")
    builder.add_document(Transaction("a", "b", 5.0))
    builder.add_document(VotingResult("vote-1", {"yes": 1}))
    block = builder.build()
    return block.to_dict()


def test_network_message_roundtrip() -> None:
    payload = {"value": 123}
    msg = NetworkMessage(type=MessageType.TRANSACTION, payload=payload, signature="sig")
    encoded = msg.to_json()
    decoded = NetworkMessage.from_json(encoded)
    assert decoded.type == MessageType.TRANSACTION
    assert decoded.payload == payload
    assert decoded.signature == "sig"


def test_document_from_dict_variants() -> None:
    tx = document_from_dict({"type": "Transaction", "sender": "a", "recipient": "b", "amount": 1.5})
    vr = document_from_dict({"type": "VotingResult", "voting_id": "v1", "results": {"x": 2}})
    other = document_from_dict({"type": "Custom", "field": "value"})
    assert tx.get_json_data()
    assert vr.get_json_data()
    assert other.get_json_data()


def test_block_from_dict_valid_and_invalid() -> None:
    block_data = build_block_dict()
    block = block_from_dict(block_data)
    assert block is not None
    invalid_block = dict(block_data)
    invalid_block["hash"] = "wrong"
    assert block_from_dict(invalid_block) is None


def test_discovery_service_queue_usage() -> None:
    service = DiscoveryService("node", 8000)
    service._found_peers = Queue()
    service._found_peers.put(("127.0.0.1", 8001))
    service._found_peers.put(("127.0.0.1", 8002))
    peers = service.get_new_peers()
    assert peers == [("127.0.0.1", 8001), ("127.0.0.1", 8002)]
    assert service.get_new_peers() == []


def test_synchronizer_requests_blocks_when_peer_is_ahead() -> None:
    chain = StubChain()
    peer = StubPeer(remote_height=5, sent=[])

    class StubPeers:
        def get_best_peer(self) -> Optional[StubPeer]:
            return peer

    synchronizer = BlockSynchronizer(chain, StubPeers())
    assert synchronizer.sync_blockchain() is True
    assert peer.sent
    assert peer.sent[0].type == MessageType.GET_BLOCKS
    assert peer.sent[0].payload["from_height"] == chain.get_height()


def test_peer_manager_handles_get_blocks() -> None:
    chain = StubChain()
    chain.block_store.append(block_from_dict(build_block_dict()))
    manager = PeerManager(chain, DummyIdentityManager())

    class Sender:
        def __init__(self) -> None:
            self.sent: List[NetworkMessage] = []

        def send(self, msg: NetworkMessage) -> None:
            self.sent.append(msg)

    sender = Sender()
    msg = NetworkMessage(type=MessageType.GET_BLOCKS, payload={"from_height": 0})
    manager.on_message(msg, sender)
    assert sender.sent
    response = sender.sent[0]
    assert response.type == MessageType.BLOCKS_RESPONSE
    assert response.payload["blocks"]


def test_peer_manager_handles_transaction_and_block() -> None:
    chain = StubChain()
    manager = PeerManager(chain, DummyIdentityManager())
    tx_msg = NetworkMessage(type=MessageType.TRANSACTION, payload={"id": "tx1"})
    manager.on_message(tx_msg, manager)
    assert chain.received_transactions == [{"id": "tx1"}]

    block_data = build_block_dict()
    block_msg = NetworkMessage(type=MessageType.BLOCK, payload=block_data)
    manager.on_message(block_msg, manager)
    assert chain.received_blocks
