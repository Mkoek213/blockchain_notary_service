import json
import logging
import socket
import threading
from queue import Empty, Queue
from typing import Any, Dict, Optional, Protocol, Tuple, TYPE_CHECKING

from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding

from blockchain_core.interfaces import IBlockchainInterface

from .types import MessageType, PeerState
if TYPE_CHECKING:
    from security.identity_manager import IdentityManager

from .message import NetworkMessage

logger = logging.getLogger(__name__)


class IConnectionListener(Protocol):
    def on_message(self, msg: NetworkMessage, sender: "IPeerConnection") -> None:
        ...

    def on_disconnect(self, sender: "IPeerConnection") -> None:
        ...

    def on_handshake_complete(self, sender: "IPeerConnection") -> None:
        ...


class IPeerConnection(Protocol):
    remote_height: int
    remote_hash: str
    peer_id: str
    address: Tuple[str, int]
    remote_endpoint: Tuple[str, int]

    def send(self, msg: NetworkMessage) -> None:
        ...

    def close(self) -> None:
        ...


class PeerConnection(IPeerConnection):
    def __init__(
        self,
        sock: socket.socket,
        address: Tuple[str, int],
        listener: IConnectionListener,
        identity_manager: Optional["IdentityManager"],
        chain: IBlockchainInterface,
        local_port: int,
    ) -> None:
        if identity_manager is None:
            raise ValueError("identity_manager is required")
        self.socket = sock
        self.address = address
        self.listener = listener
        self.identity_manager = identity_manager
        self.chain = chain
        self.local_port = local_port
        self.state = PeerState.CONNECTING
        self.out_queue: Queue[NetworkMessage] = Queue()
        self.remote_height = 0
        self.remote_hash = ""
        self.peer_id = ""
        self.remote_certificate_pem: Optional[str] = None
        self.remote_endpoint = self.address
        self._stop_event = threading.Event()
        self._sender_thread = threading.Thread(target=self._send_loop, daemon=True)
        self._receiver_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._sender_thread.start()
        self._receiver_thread.start()
        self._perform_handshake()

    def send(self, msg: NetworkMessage) -> None:
        self.out_queue.put(msg)
        logger.info("queued message %s to %s", msg.type.value, self.address)

    def close(self) -> None:
        if self._stop_event.is_set():
            return
        self._stop_event.set()
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.socket.close()
        except OSError:
            pass

    def _send_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                msg = self.out_queue.get(timeout=0.5)
            except Empty:
                continue
            data = self._prepare_message(msg)
            if data is None:
                continue
            try:
                self.socket.sendall(data)
            except OSError:
                self._stop_event.set()
                self.listener.on_disconnect(self)
                return
            logger.info("sent message %s to %s", msg.type.value, self.address)

    def _listen_loop(self) -> None:
        buffer = ""
        while not self._stop_event.is_set():
            try:
                chunk = self.socket.recv(4096)
            except OSError:
                self._stop_event.set()
                self.listener.on_disconnect(self)
                return
            if not chunk:
                self._stop_event.set()
                self.listener.on_disconnect(self)
                return
            buffer += chunk.decode("utf-8")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line:
                    continue
                try:
                    msg = NetworkMessage.from_json(line)
                except Exception:
                    continue
                if msg.type == MessageType.HANDSHAKE:
                    self._handle_handshake(msg)
                    continue
                if not self._verify_message(msg):
                    continue
                logger.info("received message %s from %s", msg.type.value, self.address)
                self.listener.on_message(msg, self)

    def _perform_handshake(self) -> None:
        payload = {
            "node_id": self._get_node_id(),
            "height": self.chain.get_height(),
            "latest_hash": self.chain.get_latest_block_hash(),
            "port": self.local_port,
            "certificate": self._get_certificate_pem(),
        }
        msg = NetworkMessage(type=MessageType.HANDSHAKE, payload=payload)
        self.send(msg)

    def _handle_handshake(self, msg: NetworkMessage) -> None:
        payload = msg.payload
        certificate_pem = payload.get("certificate", "")
        if not certificate_pem and self.identity_manager is not None:
            self.close()
            return
        if not self._validate_handshake(msg, certificate_pem):
            self.close()
            return
        self.remote_height = int(payload.get("height", 0))
        self.remote_hash = str(payload.get("latest_hash", ""))
        self.peer_id = str(payload.get("node_id", ""))
        self.remote_certificate_pem = certificate_pem if certificate_pem else None
        remote_port = int(payload.get("port", self.address[1]))
        self.remote_endpoint = (self.address[0], remote_port)
        self.state = PeerState.READY
        logger.info("handshake completed with %s", self.address)
        self.listener.on_handshake_complete(self)

    def _get_node_id(self) -> str:
        cert = self.identity_manager.get_self_certificate()
        if cert is None:
            return ""
        return cert.subject.rfc4514_string()

    def _get_certificate_pem(self) -> str:
        cert = self.identity_manager.get_self_certificate()
        if cert is None:
            return ""
        return cert.public_bytes(encoding=Encoding.PEM).decode("utf-8")

    def _prepare_message(self, msg: NetworkMessage) -> Optional[bytes]:
        if msg.signature == "":
            msg.signature = self._sign_message(msg)
        try:
            return (msg.to_json() + "\n").encode("utf-8")
        except Exception:
            return None

    def _sign_message(self, msg: NetworkMessage) -> str:
        if self.identity_manager is None:
            return ""
        data = self._get_signable_bytes(msg)
        signature = self.identity_manager.sign_data(data)
        return signature.hex()

    def _verify_message(self, msg: NetworkMessage) -> bool:
        if not msg.signature:
            return False
        if not self.remote_certificate_pem:
            return False
        try:
            cert = x509.load_pem_x509_certificate(self.remote_certificate_pem.encode("utf-8"))
        except Exception:
            return False
        data = self._get_signable_bytes(msg)
        try:
            signature = bytes.fromhex(msg.signature)
        except ValueError:
            return False
        return self.identity_manager.verify_peer_signature(data, signature, cert)

    def _validate_handshake(self, msg: NetworkMessage, certificate_pem: str) -> bool:
        if not certificate_pem:
            return False
        try:
            cert = x509.load_pem_x509_certificate(certificate_pem.encode("utf-8"))
        except Exception:
            return False
        if not self.identity_manager.validate_peer(cert):
            return False
        if not msg.signature:
            return False
        data = self._get_signable_bytes(msg)
        try:
            signature = bytes.fromhex(msg.signature)
        except ValueError:
            return False
        return self.identity_manager.verify_peer_signature(data, signature, cert)

    def _get_signable_bytes(self, msg: NetworkMessage) -> bytes:
        payload = {"type": msg.type.value, "payload": msg.payload}
        return json.dumps(payload, sort_keys=True).encode("utf-8")
