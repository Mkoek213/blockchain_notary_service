import json
import logging
import socket
import threading
import time
from queue import Queue
from typing import Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DiscoveryService:
    def __init__(
        self,
        node_id: str,
        tcp_port: int,
        discovery_port: int = 9999,
        broadcast_interval: float = 2.0,
        active_peers_provider: Optional[Callable[[], int]] = None,
        max_peers: int = 3,
        peer_filter: Optional[Callable[[str, int], bool]] = None,
    ) -> None:
        self.node_id = node_id
        self.tcp_port = tcp_port
        self.discovery_port = discovery_port
        self.broadcast_interval = broadcast_interval
        self.active_peers_provider = active_peers_provider
        self.max_peers = max_peers
        self.peer_filter = peer_filter
        self._found_peers: Queue[Tuple[str, int, str]] = Queue()
        self._seen_peers: Dict[str, Tuple[str, int, float]] = {}
        self._seen_ttl = 30.0
        self._stop_event = threading.Event()
        self._listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)

    def start_listener(self) -> None:
        if not self._listener_thread.is_alive():
            logger.info("discovery listener starting on port %s", self.discovery_port)
            self._listener_thread.start()

    def broadcast_presence(self) -> None:
        if not self._broadcast_thread.is_alive():
            logger.info("discovery broadcast starting on port %s", self.discovery_port)
            self._broadcast_thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        logger.info("discovery stopped")

    def get_new_peers(self) -> List[Tuple[str, int]]:
        peers: List[Tuple[str, int, str]] = []
        while not self._found_peers.empty():
            peers.append(self._found_peers.get())
        return peers

    def _listen_loop(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("", self.discovery_port))
            sock.settimeout(1.0)
            while not self._stop_event.is_set():
                try:
                    data, addr = sock.recvfrom(2048)
                except socket.timeout:
                    continue
                try:
                    payload = json.loads(data.decode("utf-8"))
                except Exception:
                    continue
                node_id = str(payload.get("node_id", ""))
                if not node_id or node_id == self.node_id:
                    continue
                port = int(payload.get("port", 0))
                if port <= 0:
                    continue
                advertised_ip = payload.get("ip") or addr[0]
                now = time.monotonic()
                last_seen = self._seen_peers.get(node_id)
                if last_seen is not None and now - last_seen[2] < self._seen_ttl:
                    continue
                if self.peer_filter is not None and not self.peer_filter(advertised_ip, port):
                    self._seen_peers[node_id] = (advertised_ip, port, now)
                    continue
                self._seen_peers[node_id] = (advertised_ip, port, now)
                logger.info("discovered peer %s:%s", advertised_ip, port)
                self._found_peers.put((advertised_ip, port, node_id))
        finally:
            sock.close()

    def _broadcast_loop(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        advertised_ip = socket.gethostbyname(socket.gethostname())
        payload = json.dumps(
            {"node_id": self.node_id, "port": self.tcp_port, "ip": advertised_ip}
        ).encode("utf-8")
        try:
            while not self._stop_event.is_set():
                if self.active_peers_provider is not None:
                    if self.active_peers_provider() >= self.max_peers:
                        time.sleep(self.broadcast_interval)
                        continue
                sock.sendto(payload, ("<broadcast>", self.discovery_port))
                logger.debug("broadcasted presence")
                time.sleep(self.broadcast_interval)
        finally:
            sock.close()
