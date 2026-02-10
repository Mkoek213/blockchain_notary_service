"""
Blockchain Core Module
Moduł główny implementujący podstawową funkcjonalność blockchain dla serwisu notarialnego.
"""

from .block_builder import Block, BlockBuilder
from .blockchain import Blockchain
from .crypto_service import ICryptoService
from .interfaces import INotaryValidator, IStorageProvider

# Rozszerzone interfejsy dla zespołów
from .interfaces import (
    DocumentType,
    EventType,
    IBlockchainInterface,
    IBusinessLogicModule,
    ICertificateValidator,
    IDocumentFactory,
    IIdentityManager,
    IKeyStore,
    ILedgerRepository,
    IWorldStateManager,
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


_NETWORK_EXPORTS = {
    "INetworkModule",
    "IConnectionListener",
    "MessageType",
    "PeerState",
}


def __getattr__(name: str):
    if name not in _NETWORK_EXPORTS:
        raise AttributeError(name)
    from . import interfaces as _interfaces

    return getattr(_interfaces, name)
