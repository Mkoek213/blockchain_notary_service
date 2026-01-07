"""
Blockchain Core Module
Moduł główny implementujący podstawową funkcjonalność blockchain dla serwisu notarialnego.
"""

from .block_builder import Block, BlockBuilder
from .blockchain import Blockchain
from .crypto_service import ICryptoService
from .event_bus import EventBus
from .interfaces import INotaryValidator, IStorageProvider

# Rozszerzone interfejsy dla zespołów
from .interfaces_extended import (
    DocumentType,
    EventType,
    IBlockchainInterface,
    IBusinessLogicModule,
    ICertificateValidator,
    IConnectionListener,
    IDocumentFactory,
    IIdentityManager,
    IKeyStore,
    ILedgerRepository,
    INetworkModule,
    IWorldStateManager,
    MessageType,
    PeerState,
)
from .notarial_document import NotarialDocument, Transaction, VotingResult

__all__ = [
    # Blockchain Core
    "Block",
    "BlockBuilder",
    "Blockchain",
    # Dokumenty notarialne - przykładowe implementacje
    "NotarialDocument",
    "Transaction",
    "VotingResult",
    # Podstawowe interfejsy
    "IStorageProvider",
    "IConsensusProvider",
    "INotaryValidator",
    "ICryptoService",
    # System zdarzeń
    "EventBus",
    "IEventBus",
    "EventType",
    # Interfejsy dla Business Logic
    "IBusinessLogicModule",
    "IDocumentFactory",
    "DocumentType",
    # Interfejsy dla Network
    "INetworkModule",
    "IConnectionListener",
    "IBlockchainInterface",
    "MessageType",
    "PeerState",
    # Interfejsy dla Security
    "IIdentityManager",
    "ICertificateValidator",
    "IKeyStore",
    # Interfejsy dla Storage
    "IWorldStateManager",
    "ILedgerRepository",
]

__version__ = "0.4.0"
