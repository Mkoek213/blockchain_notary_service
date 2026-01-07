"""
Interfejs NotarialDocument i implementacje dla różnych typów dokumentów notarialnych.
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class NotarialDocument(ABC):
    """
    Interfejs dla dokumentów notarialnych.
    Wszystkie dokumenty przechowywane w blockchain muszą implementować ten interfejs.
    """

    @abstractmethod
    def get_json_data(self) -> str:
        """
        Zwraca reprezentację JSON dokumentu.

        Returns:
            String JSON reprezentujący dokument
        """
        pass

    @abstractmethod
    def get_signatures(self) -> List[str]:
        """
        Zwraca listę podpisów cyfrowych dokumentu.

        Returns:
            Lista podpisów
        """
        pass


class Transaction(NotarialDocument):
    """
    Klasa reprezentująca transakcję finansową w systemie notarialnym.
    """

    def __init__(self, sender: str, recipient: str, amount: float):
        """
        Inicjalizuje transakcję.

        Args:
            sender: Adres nadawcy
            recipient: Adres odbiorcy
            amount: Kwota transakcji
        """
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self._signatures: List[str] = []

    def add_signature(self, signature: str) -> None:
        """Dodaje podpis do transakcji."""
        self._signatures.append(signature)

    def get_json_data(self) -> str:
        """Zwraca reprezentację JSON transakcji."""
        data = {
            "type": "Transaction",
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "signatures": self._signatures,
        }
        return json.dumps(data, sort_keys=True)

    def get_signatures(self) -> List[str]:
        """Zwraca listę podpisów transakcji."""
        return self._signatures.copy()

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje transakcję do słownika."""
        return {
            "type": "Transaction",
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "signatures": self._signatures,
        }


class VotingResult(NotarialDocument):
    """
    Klasa reprezentująca wynik głosowania w systemie notarialnym.
    """

    def __init__(self, voting_id: str, results: Dict[str, int]):
        """
        Inicjalizuje wynik głosowania.

        Args:
            voting_id: Unikalny identyfikator głosowania
            results: Mapa wyników (opcja -> liczba głosów)
        """
        self.voting_id = voting_id
        self.results = results
        self._signatures: List[str] = []

    def add_signature(self, signature: str) -> None:
        """Dodaje podpis do wyniku głosowania."""
        self._signatures.append(signature)

    def get_json_data(self) -> str:
        """Zwraca reprezentację JSON wyniku głosowania."""
        data = {
            "type": "VotingResult",
            "voting_id": self.voting_id,
            "results": self.results,
            "signatures": self._signatures,
        }
        return json.dumps(data, sort_keys=True)

    def get_signatures(self) -> List[str]:
        """Zwraca listę podpisów wyniku głosowania."""
        return self._signatures.copy()

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje wynik głosowania do słownika."""
        return {
            "type": "VotingResult",
            "voting_id": self.voting_id,
            "results": self.results,
            "signatures": self._signatures,
        }
