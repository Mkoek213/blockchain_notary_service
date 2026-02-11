"""
Walidator dokumentów notarialnych dla systemu blockchain.

Klasa NotaryValidator implementuje interfejs INotaryValidator z blockchain_core.
Odpowiada za walidację strukturalną dokumentów, weryfikację podpisów cyfrowych
(delegowaną do ICryptoService zgodnie z modelem PoA) oraz generowanie
deterministycznych hashy dokumentów.
"""

import hashlib
import json
from typing import Any, Dict, Optional

# Dodajemy ścieżkę do blockchain_core
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from blockchain_core import INotaryValidator
from blockchain_core.crypto_service import ICryptoService


class NotaryValidator(INotaryValidator):
    """
    Walidator dokumentów notarialnych (implementacja INotaryValidator).

    Realizuje trzy funkcje:
    1. Walidacja strukturalna dokumentu (wymagane pola, poprawność typów)
    2. Weryfikacja podpisu cyfrowego (delegowana do ICryptoService - PoA/X.509)
    3. Generowanie deterministycznego hasha dokumentu (SHA-256)

    Weryfikacja podpisów jest zgodna z modelem Proof of Authority opisanym
    w dokumentacji - podpis cyfrowy autora jest walidowany przez CryptoService,
    który obsługuje kryptografię asymetryczną (klucze prywatne/publiczne).
    """

    # Znane typy dokumentów i ich wymagane pola
    _REQUIRED_FIELDS = {
        "CompanyRegistration": ["company_id", "name"],
        "SharesAllocation": ["account_id", "company_id", "shares"],
        "BalanceUpdate": ["account_id", "balance"],
        "SharesTransfer": ["seller", "buyer", "company_id", "shares_count", "price_per_share"],
        "Transaction": ["sender", "recipient", "amount"],
        "VotingResult": ["voting_id", "results"],
        "Resolution": ["resolution_id", "company_id", "resolution_type", "votes_for", "votes_against"],
        "Dividend": ["company_id", "amount_per_share", "total_amount", "record_date"],
    }

    def __init__(self, crypto_service: Optional[ICryptoService] = None):
        """
        Inicjalizuje walidator z opcjonalnym serwisem kryptograficznym.

        Args:
            crypto_service: Instancja ICryptoService do weryfikacji podpisów.
                            Jeśli None, weryfikacja podpisów będzie niedostępna.
        """
        self._crypto_service = crypto_service

    # ========================================================================
    # Implementacja INotaryValidator
    # ========================================================================

    def validate_document(self, document_data: Dict[str, Any]) -> bool:
        """
        Waliduje dokument notarialny pod kątem strukturalnym.

        Sprawdza:
        1. Czy dokument zawiera pole 'type'
        2. Czy typ dokumentu jest znany
        3. Czy wszystkie wymagane pola dla danego typu są obecne
        4. Czy wartości pól mają poprawne typy i zakresy

        Args:
            document_data: Dane dokumentu do walidacji

        Returns:
            True jeśli dokument jest strukturalnie poprawny
        """
        # Sprawdź obecność typu
        if not isinstance(document_data, dict):
            return False

        doc_type = document_data.get("type")
        if not doc_type:
            return False

        # Sprawdź czy typ jest znany
        if doc_type not in self._REQUIRED_FIELDS:
            return False

        # Sprawdź wymagane pola
        required = self._REQUIRED_FIELDS[doc_type]
        if not all(field in document_data for field in required):
            return False

        # Walidacja specyficzna dla typu
        return self._validate_type_specific(doc_type, document_data)

    def verify_signature(
        self, document_data: Dict[str, Any], signature: str, public_key: str
    ) -> bool:
        """
        Weryfikuje podpis cyfrowy dokumentu.

        Deleguje weryfikację do ICryptoService, który implementuje
        kryptografię asymetryczną zgodnie z modelem Proof of Authority.
        W systemie produkcyjnym używa certyfikatów X.509 wydanych
        przez Izbę Notarialną (CA).

        Args:
            document_data: Dane dokumentu
            signature: Podpis cyfrowy do weryfikacji
            public_key: Klucz publiczny notariusza (z certyfikatu X.509)

        Returns:
            True jeśli podpis jest poprawny
        """
        if self._crypto_service is None:
            return False

        if not signature or not public_key:
            return False

        # Deleguj weryfikację do CryptoService (PoA)
        # CryptoService obsługuje kryptografię asymetryczną
        return self._crypto_service.verify_signature(
            block_data=document_data,
            signature=signature,
            public_key=public_key,
        )

    def get_document_hash(self, document_data: Dict[str, Any]) -> str:
        """
        Generuje deterministyczny hash SHA-256 dokumentu.

        Używa posortowanego JSON-a (sort_keys=True) aby zapewnić,
        że ten sam dokument zawsze generuje identyczny hash,
        niezależnie od kolejności kluczy w słowniku.

        Args:
            document_data: Dane dokumentu

        Returns:
            Hash SHA-256 jako string hex (64 znaki)
        """
        # Sortowanie kluczy gwarantuje deterministyczność
        data_string = json.dumps(document_data, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(data_string.encode("utf-8")).hexdigest()

    # ========================================================================
    # Metody pomocnicze - walidacja specyficzna dla typu
    # ========================================================================

    def _validate_type_specific(self, doc_type: str, data: Dict[str, Any]) -> bool:
        """
        Wykonuje walidację specyficzną dla danego typu dokumentu.

        Args:
            doc_type: Typ dokumentu
            data: Dane dokumentu

        Returns:
            True jeśli dane spełniają reguły walidacji typu
        """
        if doc_type == "SharesTransfer":
            return self._validate_shares_transfer(data)
        elif doc_type == "Transaction":
            return self._validate_transaction(data)
        elif doc_type in {"CompanyRegistration", "SharesAllocation", "BalanceUpdate"}:
            return True
        elif doc_type == "VotingResult":
            return self._validate_voting_result(data)
        elif doc_type == "Resolution":
            return self._validate_resolution(data)
        elif doc_type == "Dividend":
            return self._validate_dividend(data)

        return True

    def _validate_shares_transfer(self, data: Dict[str, Any]) -> bool:
        """Waliduje dokument transferu udziałów."""
        if not isinstance(data.get("shares_count"), int) or data["shares_count"] <= 0:
            return False
        if not isinstance(data.get("price_per_share"), (int, float)) or data["price_per_share"] < 0:
            return False
        if data.get("seller") == data.get("buyer"):
            return False
        return True

    def _validate_transaction(self, data: Dict[str, Any]) -> bool:
        """Waliduje transakcję finansową."""
        if not isinstance(data.get("amount"), (int, float)) or data["amount"] <= 0:
            return False
        if data.get("sender") == data.get("recipient"):
            return False
        return True

    def _validate_voting_result(self, data: Dict[str, Any]) -> bool:
        """Waliduje wynik głosowania."""
        if not isinstance(data.get("results"), dict):
            return False
        return True

    def _validate_resolution(self, data: Dict[str, Any]) -> bool:
        """Waliduje uchwałę."""
        if not isinstance(data.get("votes_for"), int) or data["votes_for"] < 0:
            return False
        if not isinstance(data.get("votes_against"), int) or data["votes_against"] < 0:
            return False
        return True

    def _validate_dividend(self, data: Dict[str, Any]) -> bool:
        """Waliduje wypłatę dywidendy."""
        if not isinstance(data.get("amount_per_share"), (int, float)) or data["amount_per_share"] <= 0:
            return False
        if not isinstance(data.get("total_amount"), (int, float)) or data["total_amount"] <= 0:
            return False
        return True
