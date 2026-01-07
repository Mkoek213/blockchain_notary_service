"""
Interfejsy dla modułów zewnętrznych blockchain core.
Te interfejsy pozwalają innym zespołom implementować swoje moduły.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class IStorageProvider(ABC):
    """
    Interfejs dla modułu przechowywania danych blockchain.
    Implementacja: zespół odpowiedzialny za storage/persistence.
    """

    @abstractmethod
    def save_block(self, block_data: Dict[str, Any]) -> bool:
        """
        Zapisuje blok do trwałego magazynu.

        Args:
            block_data: Dane bloku do zapisania

        Returns:
            True jeśli zapis się powiódł, False w przeciwnym razie
        """
        pass

    @abstractmethod
    def load_blockchain(self) -> Optional[List[Dict[str, Any]]]:
        """
        Wczytuje blockchain z magazynu.

        Returns:
            Lista bloków lub None jeśli blockchain nie istnieje
        """
        pass

    @abstractmethod
    def get_block_by_hash(self, block_hash: str) -> Optional[Dict[str, Any]]:
        """
        Pobiera blok po jego hashu.

        Args:
            block_hash: Hash bloku

        Returns:
            Dane bloku lub None jeśli nie znaleziono
        """
        pass


class INotaryValidator(ABC):
    """
    Interfejs dla modułu walidacji dokumentów notarialnych.
    Implementacja: zespół odpowiedzialny za business logic dokumentów.
    """

    @abstractmethod
    def validate_document(self, document_data: Dict[str, Any]) -> bool:
        """
        Waliduje dokument notarialny.

        Args:
            document_data: Dane dokumentu do walidacji

        Returns:
            True jeśli dokument jest poprawny
        """
        pass

    @abstractmethod
    def verify_signature(
        self, document_data: Dict[str, Any], signature: str, public_key: str
    ) -> bool:
        """
        Weryfikuje podpis cyfrowy dokumentu.

        Args:
            document_data: Dane dokumentu
            signature: Podpis do weryfikacji
            public_key: Klucz publiczny

        Returns:
            True jeśli podpis jest poprawny
        """
        pass

    @abstractmethod
    def get_document_hash(self, document_data: Dict[str, Any]) -> str:
        """
        Generuje hash dokumentu.

        Args:
            document_data: Dane dokumentu

        Returns:
            Hash dokumentu
        """
        pass
