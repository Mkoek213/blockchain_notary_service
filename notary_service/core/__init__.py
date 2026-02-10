"""Re-exports z blockchain_core dla wygodnych importów."""

from blockchain_core import (
    Block,
    BlockBuilder,
    Blockchain,
    NotarialDocument,
    Transaction,
    VotingResult,
)
from blockchain_core.crypto_service import ICryptoService
from blockchain_core.interfaces import (
    DocumentType,
    EventType,
    IBlockchainInterface,
    IBusinessLogicModule,
    ICertificateValidator,
    IDocumentFactory,
    IIdentityManager,
    IKeyStore,
    ILedgerRepository,
    INotaryValidator,
    IStorageProvider,
    IWorldStateManager,
)

__all__ = [
    "Block",
    "BlockBuilder",
    "Blockchain",
    "NotarialDocument",
    "Transaction",
    "VotingResult",
    "ICryptoService",
    "INotaryValidator",
    "IStorageProvider",
    "DocumentType",
    "EventType",
    "IBlockchainInterface",
    "IBusinessLogicModule",
    "ICertificateValidator",
    "IDocumentFactory",
    "IIdentityManager",
    "IKeyStore",
    "ILedgerRepository",
    "IWorldStateManager",
]
