import logging
import socket
import threading
import time
import uuid
from typing import Any, Dict, Optional, TYPE_CHECKING

from blockchain_core.interfaces import IBlockchainInterface

from .discovery import DiscoveryService
from .message import NetworkMessage
from .peer_manager import PeerManager
from .synchronizer import BlockSynchronizer
from .types import MessageType

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from security.identity_manager import IdentityManager


class NetworkManager:
    def __init__(
        self,
        chain: IBlockchainInterface,
        identity_manager: Optional["IdentityManager"],
        listen_port: int = 8545,
        discovery_port: int = 9999,
        target_peers: int = 3,
        max_peers: int = 10,
    ) -> None:
        if identity_manager is None:
            raise ValueError("identity_manager is required")
        self.chain = chain
        self.identity_manager = identity_manager
        self.listen_port = listen_port
        self.discovery_port = discovery_port
        self._node_id = self._get_node_id(listen_port)
        self.peer_manager = PeerManager(
            chain,
            identity_manager,
            target_peers=target_peers,
            max_peers=max_peers,
            local_port=listen_port,
            local_node_id=self._node_id,
        )
        self.synchronizer = BlockSynchronizer(chain, self.peer_manager)
        self.peer_manager.set_synchronizer(self.synchronizer)
        self.discovery = DiscoveryService(
            self._node_id,
            listen_port,
            discovery_port,
            active_peers_provider=self.peer_manager.get_peer_count,
            max_peers=target_peers,
            peer_filter=lambda ip, port: not self.peer_manager.is_known_address(ip, port),
        )
        self._server_socket: Optional[socket.socket] = None
        self._server_thread = threading.Thread(target=self._server_loop, daemon=True)
        self._discovery_thread = threading.Thread(target=self._discovery_loop, daemon=True)
        self._sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._stop_event = threading.Event()

    def start(self, port: int = 8545) -> None:
        self.listen_port = port
        self.discovery.tcp_port = port
        self.peer_manager.local_port = port
        self._node_id = self._get_node_id(port)
        self.discovery.node_id = self._node_id
        logger.info("network manager starting on port %s", port)
        if not self._server_thread.is_alive():
            self._server_thread.start()
        self.discovery.start_listener()
        self.discovery.broadcast_presence()
        if not self._discovery_thread.is_alive():
            self._discovery_thread.start()
        if not self._sync_thread.is_alive():
            self._sync_thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self.discovery.stop()
        if self._server_socket is not None:
            try:
                self._server_socket.close()
            except OSError:
                pass
        logger.info("network manager stopped")

    def broadcast_block(self, block: Any) -> None:
        payload = block.to_dict() if hasattr(block, "to_dict") else block
        msg = NetworkMessage(type=MessageType.BLOCK, payload=payload)
        self.peer_manager.broadcast(msg)
        logger.info("broadcasted block")

    def broadcast_transaction(self, transaction: Any) -> None:
        payload = transaction.to_dict() if hasattr(transaction, "to_dict") else transaction
        msg = NetworkMessage(type=MessageType.TRANSACTION, payload=payload)
        self.peer_manager.broadcast(msg)
        logger.info("broadcasted transaction")

    def broadcast_tx(self, tx: Dict[str, Any]) -> None:
        self.broadcast_transaction(tx)

    def synchronize_chain(self) -> bool:
        return self.synchronizer.sync_blockchain()

    def get_peer_count(self) -> int:
        return len(self.peer_manager.peers)

    def _discovery_loop(self) -> None:
        while not self._stop_event.is_set():
            peers = self.discovery.get_new_peers()
            for ip, port, node_id in peers:
                self.peer_manager.add_candidate(ip, port, node_id)
            self.peer_manager.maintain_connections()
            time.sleep(1.0)

    def _server_loop(self) -> None:
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind(("", self.listen_port))
        self._server_socket.listen(5)
        self._server_socket.settimeout(1.0)
        while not self._stop_event.is_set():
            try:
                client, address = self._server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            self.peer_manager.add_incoming_connection(client, address)

    def _sync_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.synchronizer.sync_blockchain()
            except Exception:
                pass
            time.sleep(5.0)

    def _get_node_id(self, listen_port: int) -> str:
        cert = self.identity_manager.get_self_certificate()
        if cert is None:
            return f"peer-{listen_port}-{uuid.uuid4().hex[:8]}"
        return cert.subject.rfc4514_string()
