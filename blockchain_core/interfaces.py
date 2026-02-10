"""
Interfejsy dla modułów zewnętrznych blockchain core.
Te interfejsy pozwalają innym zespołom implementować swoje moduły.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional


class IStorageProvider(ABC):
    @abstractmethod
    def save_block(self, block_data: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def load_blockchain(self) -> Optional[List[Dict[str, Any]]]:
        pass

    @abstractmethod
    def get_block_by_hash(self, block_hash: str) -> Optional[Dict[str, Any]]:
        pass


class INotaryValidator(ABC):
    @abstractmethod
    def validate_document(self, document_data: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def verify_signature(
        self, document_data: Dict[str, Any], signature: str, public_key: str
    ) -> bool:
        pass

    @abstractmethod
    def get_document_hash(self, document_data: Dict[str, Any]) -> str:
        pass


class DocumentType(Enum):
    TRANSACTION = "transaction"
    VOTING_RESULT = "voting_result"
    CONTRACT = "contract"
    SHARES_TRANSFER = "shares_transfer"
    PROPERTY_DEED = "property_deed"


class IDocumentFactory(ABC):
    @abstractmethod
    def create_document(self, document_data: Dict[str, Any]):
        pass

    @abstractmethod
    def validate_document_data(self, document_data: Dict[str, Any]) -> bool:
        pass


class IBusinessLogicModule(ABC):
    @abstractmethod
    def validate_transaction(self, transaction_data: Dict[str, Any], blockchain_state: Any) -> bool:
        pass

    @abstractmethod
    def execute_smart_contract(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def check_double_spending(self, document_id: str) -> bool:
        pass

    @abstractmethod
    def validate_shares_transfer(
        self, sender: str, recipient: str, shares: int, company_id: str
    ) -> bool:
        pass


class IBlockchainInterface(ABC):
    @abstractmethod
    def get_height(self) -> int:
        pass

    @abstractmethod
    def get_last_block(self):
        pass

    @abstractmethod
    def get_blocks_range(self, start: int, end: int) -> List[Any]:
        pass

    @abstractmethod
    def validate_and_add_block(self, block: Any) -> bool:
        pass

    @abstractmethod
    def get_latest_block_hash(self) -> str:
        pass

    @abstractmethod
    def has_block(self, hash: str) -> bool:
        pass

    @abstractmethod
    def handle_transactions(self, tx_data: dict) -> None:
        pass

    @abstractmethod
    def get_blocks_from(self, height: int) -> List[Any]:
        pass


class IIdentityManager(ABC):
    @abstractmethod
    def load_certificate(self, cert_path: str, key_path: str, password: str) -> bool:
        pass

    @abstractmethod
    def get_node_id(self) -> str:
        pass

    @abstractmethod
    def get_private_key(self) -> Any:
        pass

    @abstractmethod
    def get_certificate(self) -> Any:
        pass

    @abstractmethod
    def sign_data(self, data: bytes) -> bytes:
        pass


class ICertificateValidator(ABC):
    @abstractmethod
    def validate_certificate(self, certificate: Any) -> bool:
        pass

    @abstractmethod
    def is_trusted(self, certificate: Any) -> bool:
        pass

    @abstractmethod
    def check_revocation(self, certificate: Any) -> bool:
        pass

    @abstractmethod
    def load_trusted_certificates(self, trust_store_path: str) -> bool:
        pass


class IKeyStore(ABC):
    @abstractmethod
    def store_key(self, key_id: str, key_data: bytes, password: str) -> bool:
        pass

    @abstractmethod
    def load_key(self, key_id: str, password: str) -> Optional[bytes]:
        pass

    @abstractmethod
    def delete_key(self, key_id: str) -> bool:
        pass


class IWorldStateManager(ABC):
    @abstractmethod
    def get_balance(self, account_id: str) -> float:
        pass

    @abstractmethod
    def get_shares(self, account_id: str, company_id: str) -> int:
        pass

    @abstractmethod
    def update_state(self, block: Any) -> bool:
        pass

    @abstractmethod
    def rollback_to_height(self, height: int) -> bool:
        pass

    @abstractmethod
    def get_state_root(self) -> str:
        pass


class ILedgerRepository(ABC):
    @abstractmethod
    def append_block(self, block: Any) -> bool:
        pass

    @abstractmethod
    def get_block_by_height(self, height: int) -> Optional[Any]:
        pass

    @abstractmethod
    def get_block_by_hash(self, block_hash: str) -> Optional[Any]:
        pass

    @abstractmethod
    def get_full_chain(self) -> List[Any]:
        pass


class EventType(Enum):
    BLOCK_MINED = "block_mined"
    BLOCK_RECEIVED = "block_received"
    TRANSACTION_RECEIVED = "transaction_received"
    PEER_CONNECTED = "peer_connected"
    PEER_DISCONNECTED = "peer_disconnected"
    CHAIN_SYNCHRONIZED = "chain_synchronized"
    STATE_UPDATED = "state_updated"


_NETWORK_EXPORTS = {
    "MessageType",
    "PeerState",
    "NetworkMessage",
    "IPeerConnection",
    "IConnectionListener",
    "PeerConnection",
    "PeerManager",
    "BlockSynchronizer",
    "DiscoveryService",
    "NetworkManager",
    "INetworkModule",
}


def __getattr__(name: str) -> Any:
    if name not in _NETWORK_EXPORTS:
        raise AttributeError(name)
    from network.discovery import DiscoveryService
    from network.message import NetworkMessage
    from network.network_manager import NetworkManager
    from network.peer_connection import IConnectionListener, IPeerConnection, PeerConnection
    from network.peer_manager import PeerManager
    from network.synchronizer import BlockSynchronizer
    from network.types import MessageType, PeerState

    exports = {
        "MessageType": MessageType,
        "PeerState": PeerState,
        "NetworkMessage": NetworkMessage,
        "IPeerConnection": IPeerConnection,
        "IConnectionListener": IConnectionListener,
        "PeerConnection": PeerConnection,
        "PeerManager": PeerManager,
        "BlockSynchronizer": BlockSynchronizer,
        "DiscoveryService": DiscoveryService,
        "NetworkManager": NetworkManager,
        "INetworkModule": NetworkManager,
    }
    globals().update(exports)
    return exports[name]
