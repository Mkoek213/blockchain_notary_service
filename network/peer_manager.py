import socket
import threading
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from blockchain_core.interfaces import IBlockchainInterface

from .block_adapter import block_from_dict
from .message import NetworkMessage
from .peer_connection import IConnectionListener, IPeerConnection, PeerConnection
from .types import MessageType


if TYPE_CHECKING:
    from security.identity_manager import IdentityManager


class PeerManager(IConnectionListener):
    def __init__(
        self,
        chain: IBlockchainInterface,
        identity_manager: Optional["IdentityManager"],
        max_peers: int = 3,
        local_port: int = 0,
    ) -> None:
        self.chain = chain
        self.identity_manager = identity_manager
        self.max_peers = max_peers
        self.local_port = local_port
        self.peers: Dict[str, IPeerConnection] = {}
        self.pending_peers: List[IPeerConnection] = []
        self._lock = threading.Lock()
        self.synchronizer = None

    def set_synchronizer(self, synchronizer: object) -> None:
        self.synchronizer = synchronizer

    def connect_to(self, ip: str, port: int) -> None:
        with self._lock:
            if len(self.peers) + len(self.pending_peers) >= self.max_peers:
                return
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.connect((ip, port))
            sock.settimeout(None)
        except OSError:
            return
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

    def add_incoming_connection(self, sock: socket.socket, address: Tuple[str, int]) -> None:
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

    def broadcast(self, msg: NetworkMessage) -> None:
        with self._lock:
            peers = list(self.peers.values())
        for peer in peers:
            peer.send(msg)

    def send_direct(self, peer_id: str, msg: NetworkMessage) -> None:
        with self._lock:
            peer = self.peers.get(peer_id)
        if peer is not None:
            peer.send(msg)

    def get_best_peer(self) -> Optional[IPeerConnection]:
        with self._lock:
            if not self.peers:
                return None
            return max(self.peers.values(), key=lambda p: p.remote_height)

    def on_message(self, msg: NetworkMessage, sender: IPeerConnection) -> None:
        if msg.type == MessageType.TRANSACTION:
            self.chain.handle_transactions(msg.payload)
            return
        if msg.type == MessageType.BLOCK:
            block = block_from_dict(msg.payload)
            if block is None:
                return
            self.chain.validate_and_add_block(block)
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
            if sender.peer_id and sender.peer_id in self.peers:
                del self.peers[sender.peer_id]
            if sender in self.pending_peers:
                self.pending_peers.remove(sender)

    def on_handshake_complete(self, sender: IPeerConnection) -> None:
        with self._lock:
            if sender.peer_id in self.peers:
                sender.close()
                return
            if len(self.peers) >= self.max_peers:
                sender.close()
                return
            self.peers[sender.peer_id] = sender
            if sender in self.pending_peers:
                self.pending_peers.remove(sender)
        print(f"[peer] connected {sender.peer_id} height={sender.remote_height}")
