"""
Interfejs dla CryptoService - usługa kryptograficzna do podpisywania bloków.
Implementacja tego interfejsu powinna być dostarczona przez zespół Security/Cryptography.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple


class ICryptoService(ABC):
    """
    Interfejs dla usługi kryptograficznej.
    Odpowiada za podpisywanie i weryfikację podpisów cyfrowych.

    UWAGA: To jest interfejs dla zespołu Security/Cryptography.
    Zespół ten powinien zaimplementować właściwe mechanizmy kryptograficzne.
    """

    @abstractmethod
    def sign_block(self, block_data: Dict[str, Any], private_key: str) -> str:
        """
        Podpisuje dane bloku kluczem prywatnym.

        Args:
            block_data: Dane bloku do podpisania
            private_key: Klucz prywatny do podpisania

        Returns:
            Podpis cyfrowy (jako string hex)
        """
        pass

    @abstractmethod
    def verify_signature(self, block_data: Dict[str, Any], signature: str, public_key: str) -> bool:
        """
        Weryfikuje podpis cyfrowy bloku.

        Args:
            block_data: Dane bloku
            signature: Podpis do weryfikacji
            public_key: Klucz publiczny

        Returns:
            True jeśli podpis jest poprawny
        """
        pass

    @abstractmethod
    def generate_key_pair(self) -> Tuple[str, str]:
        """
        Generuje parę kluczy (publiczny, prywatny).

        Returns:
            Tuple (public_key, private_key)
        """
        pass
