import json
import socket
import threading
import time
from queue import Queue
from typing import List, Tuple


class DiscoveryService:
    def __init__(
        self,
        node_id: str,
        tcp_port: int,
        discovery_port: int = 9999,
        broadcast_interval: float = 2.0,
    ) -> None:
        self.node_id = node_id
        self.tcp_port = tcp_port
        self.discovery_port = discovery_port
        self.broadcast_interval = broadcast_interval
        self._found_peers: Queue[Tuple[str, int]] = Queue()
        self._stop_event = threading.Event()
        self._listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)

    def start_listener(self) -> None:
        if not self._listener_thread.is_alive():
            self._listener_thread.start()

    def broadcast_presence(self) -> None:
        if not self._broadcast_thread.is_alive():
            self._broadcast_thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def get_new_peers(self) -> List[Tuple[str, int]]:
        peers: List[Tuple[str, int]] = []
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
                if payload.get("node_id") == self.node_id:
                    continue
                port = int(payload.get("port", 0))
                if port <= 0:
                    continue
                self._found_peers.put((addr[0], port))
        finally:
            sock.close()

    def _broadcast_loop(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        payload = json.dumps({"node_id": self.node_id, "port": self.tcp_port}).encode("utf-8")
        try:
            while not self._stop_event.is_set():
                sock.sendto(payload, ("<broadcast>", self.discovery_port))
                time.sleep(self.broadcast_interval)
        finally:
            sock.close()
