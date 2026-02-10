"""
Wzorzec Factory Method - dostawcy dokumentów notarialnych.

Architektura opiera się na abstrakcyjnym DocumentProvider, który definiuje
interfejs metody wytwórczej. Konkretyzacja następuje w:
- FinancialActionProvider (operacje kapitałowe: SharesTransfer, Dividend)
- GovernanceActionProvider (decyzje zarządcze: Resolution)

Zgodne z zasadą SRP - logika decyzyjna jest oddelegowana do wyspecjalizowanych
dostawców, eliminując centralne struktury switch-case.
"""

from abc import abstractmethod
from typing import Any, Dict

# Dodajemy ścieżkę do blockchain_core
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from blockchain_core import IDocumentFactory, NotarialDocument

from .documents import Dividend, Resolution, SharesTransfer


class DocumentProvider(IDocumentFactory):
    """
    Abstrakcyjna klasa bazowa dla dostawców dokumentów (Factory Method).

    Definiuje wspólny interfejs tworzenia i walidacji dokumentów.
    Konkretne podklasy decydują, które typy dokumentów potrafią stworzyć.
    """

    @abstractmethod
    def get_supported_types(self) -> list:
        """
        Zwraca listę typów dokumentów obsługiwanych przez tego providera.

        Returns:
            Lista stringów z nazwami obsługiwanych typów
        """
        pass

    def create_document(self, document_data: Dict[str, Any]) -> NotarialDocument:
        """
        Tworzy dokument notarialny odpowiedniego typu z walidacją.

        Args:
            document_data: Dane dokumentu, muszą zawierać klucz 'type'

        Returns:
            Instancja NotarialDocument

        Raises:
            ValueError: Jeśli dane są niepoprawne lub typ nieobsługiwany
        """
        if not self.validate_document_data(document_data):
            raise ValueError(
                f"Niepoprawne dane dokumentu: brakujące lub niewłaściwe pola"
            )

        doc_type = document_data.get("type")
        if doc_type not in self.get_supported_types():
            raise ValueError(
                f"Typ '{doc_type}' nie jest obsługiwany przez {self.__class__.__name__}. "
                f"Obsługiwane typy: {self.get_supported_types()}"
            )

        return self._create(document_data)

    @abstractmethod
    def _create(self, document_data: Dict[str, Any]) -> NotarialDocument:
        """
        Metoda wytwórcza - tworzy konkretny dokument.
        Implementowana przez podklasy.

        Args:
            document_data: Zwalidowane dane dokumentu

        Returns:
            Instancja NotarialDocument
        """
        pass

    @abstractmethod
    def validate_document_data(self, document_data: Dict[str, Any]) -> bool:
        """
        Waliduje dane przed utworzeniem dokumentu.

        Args:
            document_data: Dane do walidacji

        Returns:
            True jeśli dane są poprawne
        """
        pass


class FinancialActionProvider(DocumentProvider):
    """
    Dostawca dokumentów dla operacji kapitałowych (Factory Method).

    Obsługuje:
    - SharesTransfer: przelew udziałów w spółce
    - Dividend: wypłata dywidendy
    """

    def get_supported_types(self) -> list:
        """Zwraca typy dokumentów finansowych."""
        return ["SharesTransfer", "Dividend"]

    def validate_document_data(self, document_data: Dict[str, Any]) -> bool:
        """
        Waliduje dane dokumentu finansowego.

        Sprawdza obecność wymaganych pól i poprawność wartości
        w zależności od typu dokumentu.
        """
        if "type" not in document_data:
            return False

        doc_type = document_data["type"]

        if doc_type == "SharesTransfer":
            return self._validate_shares_transfer(document_data)
        elif doc_type == "Dividend":
            return self._validate_dividend(document_data)

        return False

    def _create(self, document_data: Dict[str, Any]) -> NotarialDocument:
        """Tworzy konkretny dokument finansowy."""
        doc_type = document_data["type"]

        if doc_type == "SharesTransfer":
            return self._create_shares_transfer(document_data)
        elif doc_type == "Dividend":
            return self._create_dividend(document_data)

        raise ValueError(f"Nieznany typ dokumentu finansowego: {doc_type}")

    # --- Tworzenie dokumentów ---

    def _create_shares_transfer(self, data: Dict[str, Any]) -> SharesTransfer:
        """Tworzy dokument transferu udziałów."""
        doc = SharesTransfer(
            seller=data["seller"],
            buyer=data["buyer"],
            company_id=data["company_id"],
            shares_count=data["shares_count"],
            price_per_share=data["price_per_share"],
        )
        for sig in data.get("signatures", []):
            doc.add_signature(sig)
        return doc

    def _create_dividend(self, data: Dict[str, Any]) -> Dividend:
        """Tworzy dokument wypłaty dywidendy."""
        doc = Dividend(
            company_id=data["company_id"],
            amount_per_share=data["amount_per_share"],
            total_amount=data["total_amount"],
            record_date=data["record_date"],
        )
        for sig in data.get("signatures", []):
            doc.add_signature(sig)
        return doc

    # --- Walidacja danych ---

    def _validate_shares_transfer(self, data: Dict[str, Any]) -> bool:
        """Waliduje dane dla transferu udziałów."""
        required = ["seller", "buyer", "company_id", "shares_count", "price_per_share"]
        if not all(f in data for f in required):
            return False

        if not isinstance(data["shares_count"], int) or data["shares_count"] <= 0:
            return False

        if not isinstance(data["price_per_share"], (int, float)) or data["price_per_share"] < 0:
            return False

        if data["seller"] == data["buyer"]:
            return False

        return True

    def _validate_dividend(self, data: Dict[str, Any]) -> bool:
        """Waliduje dane dla wypłaty dywidendy."""
        required = ["company_id", "amount_per_share", "total_amount", "record_date"]
        if not all(f in data for f in required):
            return False

        if not isinstance(data["amount_per_share"], (int, float)) or data["amount_per_share"] <= 0:
            return False

        if not isinstance(data["total_amount"], (int, float)) or data["total_amount"] <= 0:
            return False

        return True


class GovernanceActionProvider(DocumentProvider):
    """
    Dostawca dokumentów dla decyzji zarządczych (Factory Method).

    Obsługuje:
    - Resolution: uchwały i wyniki głosowań
    """

    def get_supported_types(self) -> list:
        """Zwraca typy dokumentów zarządczych."""
        return ["Resolution"]

    def validate_document_data(self, document_data: Dict[str, Any]) -> bool:
        """
        Waliduje dane dokumentu zarządczego.

        Sprawdza obecność wymaganych pól i poprawność wartości głosowania.
        """
        if "type" not in document_data:
            return False

        doc_type = document_data["type"]

        if doc_type == "Resolution":
            return self._validate_resolution(document_data)

        return False

    def _create(self, document_data: Dict[str, Any]) -> NotarialDocument:
        """Tworzy konkretny dokument zarządczy."""
        doc_type = document_data["type"]

        if doc_type == "Resolution":
            return self._create_resolution(document_data)

        raise ValueError(f"Nieznany typ dokumentu zarządczego: {doc_type}")

    # --- Tworzenie dokumentów ---

    def _create_resolution(self, data: Dict[str, Any]) -> Resolution:
        """Tworzy dokument uchwały."""
        doc = Resolution(
            resolution_id=data["resolution_id"],
            company_id=data["company_id"],
            resolution_type=data["resolution_type"],
            votes_for=data["votes_for"],
            votes_against=data["votes_against"],
        )
        for sig in data.get("signatures", []):
            doc.add_signature(sig)
        return doc

    # --- Walidacja danych ---

    def _validate_resolution(self, data: Dict[str, Any]) -> bool:
        """Waliduje dane dla uchwały."""
        required = [
            "resolution_id", "company_id", "resolution_type",
            "votes_for", "votes_against",
        ]
        if not all(f in data for f in required):
            return False

        if not isinstance(data["votes_for"], int) or data["votes_for"] < 0:
            return False

        if not isinstance(data["votes_against"], int) or data["votes_against"] < 0:
            return False

        return True
