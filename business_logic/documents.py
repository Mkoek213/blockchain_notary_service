"""
Typy dokumentów notarialnych dla systemu blockchain.

Klasy dziedziczą po NotarialDocument z blockchain_core i reprezentują
konkretne operacje biznesowe: transfer udziałów, uchwały, dywidendy.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List


# Dodajemy ścieżkę do blockchain_core
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from blockchain_core import NotarialDocument


@dataclass
class SharesTransfer(NotarialDocument):
    """
    Dokument notarialny reprezentujący transfer udziałów w spółce.

    Opisuje operację zbycia udziałów przez jedną stronę na rzecz drugiej.
    Walidacja biznesowa (czy zbywca posiada wystarczającą liczbę udziałów)
    jest realizowana przez BusinessLogicModule, nie przez sam dokument.
    """

    seller: str
    buyer: str
    company_id: str
    shares_count: int
    price_per_share: float
    _signatures: List[str] = field(default_factory=list, repr=False)

    def add_signature(self, signature: str) -> None:
        """Dodaje podpis cyfrowy do dokumentu."""
        self._signatures.append(signature)

    def get_json_data(self) -> str:
        """Zwraca deterministyczną reprezentację JSON dokumentu."""
        data = {
            "type": "SharesTransfer",
            "seller": self.seller,
            "buyer": self.buyer,
            "company_id": self.company_id,
            "shares_count": self.shares_count,
            "price_per_share": self.price_per_share,
            "signatures": self._signatures,
        }
        return json.dumps(data, sort_keys=True)

    def get_signatures(self) -> List[str]:
        """Zwraca kopię listy podpisów cyfrowych."""
        return self._signatures.copy()

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje dokument do słownika."""
        return {
            "type": "SharesTransfer",
            "seller": self.seller,
            "buyer": self.buyer,
            "company_id": self.company_id,
            "shares_count": self.shares_count,
            "price_per_share": self.price_per_share,
            "signatures": self._signatures,
        }


@dataclass
class Resolution(NotarialDocument):
    """
    Dokument notarialny reprezentujący uchwałę (wynik głosowania zarządczego).

    Opisuje decyzję podjętą w ramach spółki, np. zatwierdzenie sprawozdania
    finansowego, zmiana statutu, powołanie członka zarządu.
    """

    resolution_id: str
    company_id: str
    resolution_type: str
    votes_for: int
    votes_against: int
    _signatures: List[str] = field(default_factory=list, repr=False)

    def add_signature(self, signature: str) -> None:
        """Dodaje podpis cyfrowy do dokumentu."""
        self._signatures.append(signature)

    def get_json_data(self) -> str:
        """Zwraca deterministyczną reprezentację JSON dokumentu."""
        data = {
            "type": "Resolution",
            "resolution_id": self.resolution_id,
            "company_id": self.company_id,
            "resolution_type": self.resolution_type,
            "votes_for": self.votes_for,
            "votes_against": self.votes_against,
            "signatures": self._signatures,
        }
        return json.dumps(data, sort_keys=True)

    def get_signatures(self) -> List[str]:
        """Zwraca kopię listy podpisów cyfrowych."""
        return self._signatures.copy()

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje dokument do słownika."""
        return {
            "type": "Resolution",
            "resolution_id": self.resolution_id,
            "company_id": self.company_id,
            "resolution_type": self.resolution_type,
            "votes_for": self.votes_for,
            "votes_against": self.votes_against,
            "signatures": self._signatures,
        }

    @property
    def is_passed(self) -> bool:
        """Sprawdza czy uchwała została przegłosowana (większość głosów za)."""
        return self.votes_for > self.votes_against


@dataclass
class Dividend(NotarialDocument):
    """
    Dokument notarialny reprezentujący wypłatę dywidendy.

    Opisuje decyzję o wypłacie zysku spółki do udziałowców.
    """

    company_id: str
    amount_per_share: float
    total_amount: float
    record_date: str
    _signatures: List[str] = field(default_factory=list, repr=False)

    def add_signature(self, signature: str) -> None:
        """Dodaje podpis cyfrowy do dokumentu."""
        self._signatures.append(signature)

    def get_json_data(self) -> str:
        """Zwraca deterministyczną reprezentację JSON dokumentu."""
        data = {
            "type": "Dividend",
            "company_id": self.company_id,
            "amount_per_share": self.amount_per_share,
            "total_amount": self.total_amount,
            "record_date": self.record_date,
            "signatures": self._signatures,
        }
        return json.dumps(data, sort_keys=True)

    def get_signatures(self) -> List[str]:
        """Zwraca kopię listy podpisów cyfrowych."""
        return self._signatures.copy()

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje dokument do słownika."""
        return {
            "type": "Dividend",
            "company_id": self.company_id,
            "amount_per_share": self.amount_per_share,
            "total_amount": self.total_amount,
            "record_date": self.record_date,
            "signatures": self._signatures,
        }
