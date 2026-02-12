import json
import logging
import random
import socket
import threading
import time
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from blockchain_core.interfaces import IBlockchainInterface

from .block_adapter import block_from_dict
from .message import NetworkMessage
from .peer_connection import IConnectionListener, IPeerConnection, PeerConnection
from .types import MessageType

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from security.identity_manager import IdentityManager


class PeerManager(IConnectionListener):
    def __init__(
        self,
        chain: IBlockchainInterface,
        identity_manager: Optional["IdentityManager"],
        target_peers: int = 3,
        max_peers: int = 15,
        local_port: int = 0,
        local_node_id: str = "",
    ) -> None:
        if identity_manager is None:
            raise ValueError("identity_manager is required")
        self.chain = chain
        self.identity_manager = identity_manager
        self.target_peers = target_peers
        self.max_peers = max_peers
        self.local_port = local_port
        self.local_node_id = local_node_id
        self.peers: Dict[str, IPeerConnection] = {}
        self.pending_peers: List[IPeerConnection] = []
        self._lock = threading.Lock()
        self.synchronizer = None
        self._candidates: Dict[str, Tuple[str, int, float]] = {}
        self._pending_node_ids: set[str] = set()
        self._retry_interval = 2.0
        self._disconnect_chance = 0.0
        self._seen_messages: Dict[str, float] = {}
        self._seen_ttl = 300.0
        self._stop_event = threading.Event()
        self._maintain_thread = threading.Thread(target=self._maintain_loop, daemon=True)
        self._maintain_thread.start()

    def set_synchronizer(self, synchronizer: object) -> None:
        self.synchronizer = synchronizer

    def stop(self) -> None:
        self._stop_event.set()

    def connect_to(self, ip: str, port: int) -> None:
        self.add_candidate(ip, port, None)
        self.maintain_connections()

    def add_candidate(self, ip: str, port: int, node_id: Optional[str]) -> None:
        if port <= 0:
            return
        if ip in {"127.0.0.1", "localhost"} and port == self.local_port:
            return
        if node_id:
            if node_id == self.local_node_id:
                return
            if node_id in self.peers or node_id in self._pending_node_ids:
                return
        with self._lock:
            if self._is_known_address(ip, port):
                return
            if node_id and node_id in self._candidates:
                return
            if not node_id:
                node_id = f"{ip}:{port}"
            self._candidates[node_id] = (ip, port, 0.0)
        logger.debug("candidate added %s:%s", ip, port)

    def maintain_connections(self) -> None:
        with self._lock:
            if len(self.peers) + len(self.pending_peers) >= self.target_peers:
                return
        now = time.monotonic()
        with self._lock:
            candidates = list(self._candidates.items())
        random.shuffle(candidates)
        for node_id, (ip, port, next_attempt) in candidates:
            with self._lock:
                if len(self.peers) + len(self.pending_peers) >= self.target_peers:
                    return
            if next_attempt > now:
                continue
            if self._attempt_connect(ip, port, node_id):
                with self._lock:
                    self._candidates.pop(node_id, None)
                continue
            with self._lock:
                self._candidates[node_id] = (ip, port, now + self._retry_interval)

    def _attempt_connect(self, ip: str, port: int, node_id: str) -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.connect((ip, port))
            sock.settimeout(None)
        except OSError:
            return False
        logger.info("connected tcp to %s:%s", ip, port)
        with self._lock:
            self._pending_node_ids.add(node_id)
        peer = PeerConnection(
            sock,
            (ip, port),
            self,
            self.identity_manager,
            self.chain,
            self.local_port,
        )
        with self._lock:
            self.pending_peers.append(peer)
        return True

    def add_incoming_connection(self, sock: socket.socket, address: Tuple[str, int]) -> None:
        with self._lock:
            if len(self.peers) + len(self.pending_peers) >= self.max_peers:
                logger.warning("rejected incoming %s:%s (max peers reached)", address[0], address[1])
                sock.close()
                return
        peer = PeerConnection(
            sock,
            address,
            self,
            self.identity_manager,
            self.chain,
            self.local_port,
        )
        with self._lock:
            self.pending_peers.append(peer)
            self._candidates.pop(address, None)
        logger.info("accepted incoming connection %s:%s", address[0], address[1])

    def broadcast(self, msg: NetworkMessage) -> None:
        with self._lock:
            peers = list(self.peers.values())
        for peer in peers:
            peer.send(msg)

    def broadcast_except(self, msg: NetworkMessage, exclude: IPeerConnection) -> None:
        with self._lock:
            peers = [peer for peer in self.peers.values() if peer is not exclude]
        for peer in peers:
            peer.send(msg)

    def send_direct(self, peer_id: str, msg: NetworkMessage) -> None:
        with self._lock:
            peer = self.peers.get(peer_id)
        if peer is not None:
            peer.send(msg)

    def get_peer_count(self) -> int:
        with self._lock:
            return len(self.peers)

    def is_known_address(self, ip: str, port: int) -> bool:
        with self._lock:
            return self._is_known_address(ip, port)

    def get_best_peer(self) -> Optional[IPeerConnection]:
        with self._lock:
            if not self.peers:
                return None
            return max(self.peers.values(), key=lambda p: p.remote_height)

    def on_message(self, msg: NetworkMessage, sender: IPeerConnection) -> None:
        logger.info("dispatch message %s from %s", msg.type.value, sender.peer_id)
        if msg.type in {MessageType.TRANSACTION, MessageType.BLOCK}:
            message_id = self._message_id(msg)
            if self._is_seen(message_id):
                return
            self._mark_seen(message_id)
        if msg.type == MessageType.TRANSACTION:
            self.chain.handle_transactions(msg.payload)
            self.broadcast_except(msg, sender)
            return
        if msg.type == MessageType.BLOCK:
            block = block_from_dict(msg.payload)
            if block is None:
                return
            if self.chain.validate_and_add_block(block):
                self.broadcast_except(msg, sender)
                return
            payload = {"from_height": self.chain.get_height()}
            sender.send(NetworkMessage(type=MessageType.GET_BLOCKS, payload=payload))
            return
        if msg.type == MessageType.GET_BLOCKS:
            from_height = int(msg.payload.get("from_height", 0))
            blocks = self.chain.get_blocks_from(from_height)
            payload = {"blocks": [block.to_dict() for block in blocks]}
            sender.send(NetworkMessage(type=MessageType.BLOCKS_RESPONSE, payload=payload))
            return
        if msg.type == MessageType.BLOCKS_RESPONSE:
            if self.synchronizer is not None:
                self.synchronizer.handle_block_response(msg.payload)

    def on_disconnect(self, sender: IPeerConnection) -> None:
        with self._lock:
            if sender.peer_id:
                current = self.peers.get(sender.peer_id)
                if current is sender:
                    del self.peers[sender.peer_id]
            if sender in self.pending_peers:
                self.pending_peers.remove(sender)
            if sender.peer_id:
                self._pending_node_ids.discard(sender.peer_id)
        if sender.peer_id and sender.peer_id in self.peers:
            return
        if getattr(sender, "remote_endpoint", None) is not None:
            peer_id = sender.peer_id or None
            self.add_candidate(sender.remote_endpoint[0], sender.remote_endpoint[1], peer_id)
        logger.info("peer disconnected %s", sender.peer_id)
        self.maintain_connections()

    def on_handshake_complete(self, sender: IPeerConnection) -> None:
        with self._lock:
            if sender.peer_id == self.local_node_id:
                sender.close()
                if sender in self.pending_peers:
                    self.pending_peers.remove(sender)
                return
            if sender.peer_id in self.peers:
                sender.close()
                return
            if len(self.peers) >= self.max_peers:
                sender.close()
                return
            self.peers[sender.peer_id] = sender
            self._pending_node_ids.discard(sender.peer_id)
            self._candidates.pop(sender.peer_id, None)
            if sender in self.pending_peers:
                self.pending_peers.remove(sender)
        print(f"[peer] connected {sender.peer_id} height={sender.remote_height}")
        logger.info("peer connected %s", sender.peer_id)
        self.maintain_connections()
        if self.synchronizer is not None:
            if sender.remote_height > self.chain.get_height():
                self.synchronizer.sync_blockchain()

    def _maintain_loop(self) -> None:
        while not self._stop_event.is_set():
            peer_to_drop: Optional[IPeerConnection] = None
            with self._lock:
                if self.peers and random.random() < self._disconnect_chance:
                    peer_to_drop = random.choice(list(self.peers.values()))
            if peer_to_drop is not None:
                peer_to_drop.close()
            self.maintain_connections()
            time.sleep(1.0)

    def _message_id(self, msg: NetworkMessage) -> str:
        payload = json.dumps(msg.payload, sort_keys=True, ensure_ascii=True)
        return f"{msg.type.value}:{payload}"

    def _is_seen(self, message_id: str) -> bool:
        now = time.monotonic()
        seen_at = self._seen_messages.get(message_id)
        if seen_at is None:
            return False
        if now - seen_at > self._seen_ttl:
            self._seen_messages.pop(message_id, None)
            return False
        return True

    def _mark_seen(self, message_id: str) -> None:
        now = time.monotonic()
        self._seen_messages[message_id] = now
        if len(self._seen_messages) > 10000:
            cutoff = now - self._seen_ttl
            self._seen_messages = {
                key: ts for key, ts in self._seen_messages.items() if ts >= cutoff
            }

    def _is_known_address(self, ip: str, port: int) -> bool:
        for peer in self.peers.values():
            if getattr(peer, "remote_endpoint", None) == (ip, port):
                return True
        for peer in self.pending_peers:
            if getattr(peer, "remote_endpoint", None) == (ip, port):
                return True
        return False
