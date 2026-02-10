"""
Notary Service - biblioteka integrująca moduły systemu notarialnego.

Cel: zapewnić spójny punkt wejścia bez modyfikowania istniejących modułów.
"""

from .document_registry import DocumentRegistry
from .facade import NotaryService
from .persistent_blockchain import PersistentBlockchain
from .storage import JsonLedgerRepository, JsonStorageProvider, JsonWorldStateManager

__all__ = [
    "NotaryService",
    "PersistentBlockchain",
    "DocumentRegistry",
    "JsonLedgerRepository",
    "JsonStorageProvider",
    "JsonWorldStateManager",
]
