"""
Mockowa implementacja CryptoService dla celów demonstracyjnych i testowych.
UWAGA: Zespół Security/Cryptography powinien zastąpić tę implementację właściwym rozwiązaniem.
"""

import hashlib
import json
from typing import Any, Dict, Tuple

from .crypto_service import ICryptoService


class MockCryptoService(ICryptoService):
    """
    Mockowa implementacja serwisu kryptograficznego.
    Używa prostego hashowania zamiast prawdziwej kryptografii asymetrycznej.

    UWAGA: To jest tylko przykład dla celów testowych!
    Zespół Security powinien zaimplementować właściwą kryptografię (RSA, ECDSA, itp.)
    """

    def sign_block(self, block_data: Dict[str, Any], private_key: str) -> str:
        """
        Mockowe podpisywanie bloku.
        W rzeczywistości powinno używać kryptografii asymetrycznej.

        Args:
            block_data: Dane bloku do podpisania
            private_key: Klucz prywatny (w mockowej wersji to string)

        Returns:
            Podpis jako hex string
        """
        # Serializuj dane bloku
        block_string = json.dumps(block_data, sort_keys=True)

        # Połącz z kluczem prywatnym i zahashuj
        # W prawdziwej implementacji użyj RSA/ECDSA
        data_to_sign = f"{block_string}{private_key}".encode()
        signature = hashlib.sha256(data_to_sign).hexdigest()

        return signature

    def verify_signature(self, block_data: Dict[str, Any], signature: str, public_key: str) -> bool:
        """
        Mockowa weryfikacja podpisu.

        Args:
            block_data: Dane bloku
            signature: Podpis do weryfikacji
            public_key: Klucz publiczny

        Returns:
            True jeśli podpis jest poprawny
        """
        # W mockowej wersji zakładamy że klucz publiczny == klucz prywatny
        # W prawdziwej implementacji użyj właściwej weryfikacji RSA/ECDSA
        expected_signature = self.sign_block(block_data, public_key)
        return signature == expected_signature

    def generate_key_pair(self) -> Tuple[str, str]:
        """
        Mockowa generacja pary kluczy.
        W prawdziwej implementacji użyj właściwego generatora kluczy.

        Returns:
            Tuple (public_key, private_key)
        """
        import time

        # Generuj losowy klucz na podstawie timestampu
        seed = f"{time.time()}".encode()
        key = hashlib.sha256(seed).hexdigest()

        # W mockowej wersji klucz publiczny == klucz prywatny
        # W prawdziwej implementacji to są różne klucze
        return (key, key)
