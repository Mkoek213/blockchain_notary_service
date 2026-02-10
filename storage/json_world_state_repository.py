import os
import json
from typing import Dict
from .repositories import WorldStateRepository
from .serializer import JsonSerializer
from blockchain_core.notarial_document import Transaction

class JsonWorldStateRepository(WorldStateRepository):
    """
    Implementacja repozytorium stanu świata w pliku JSON.
    Utrzymuje mapę: { "adres_portfela": saldo }
    """

    def __init__(self, file_path: str = "world_state.json"):
        self.file_path = file_path
        self.balances: Dict[str, float] = {}
        self._load_state_from_disk()

    def update_state(self, tx: Transaction) -> None:
        """
        Aktualizuje stan na podstawie transakcji.
        """
        sender = tx.sender
        recipient = tx.recipient
        amount = tx.amount

        # Pobierz aktualne salda (domyślnie 0.0)
        sender_balance = self.balances.get(sender, 0.0)
        recipient_balance = self.balances.get(recipient, 0.0)

        # Logika biznesowa - odejmij i dodaj
        # UWAGA: Tu normalnie byłaby walidacja (czy sender ma środki),
        # ale repozytorium tylko ZAPISUJE zmiany, walidator je sprawdza wcześniej.
        self.balances[sender] = sender_balance - amount
        self.balances[recipient] = recipient_balance + amount

    def rollback(self, tx: Transaction) -> None:
        """
        Cofa transakcję (odwraca działanie).
        """
        sender = tx.sender
        recipient = tx.recipient
        amount = tx.amount

        # Przywracamy środki
        self.balances[sender] = self.balances.get(sender, 0.0) + amount
        self.balances[recipient] = self.balances.get(recipient, 0.0) - amount

    def get_balance(self, address: str) -> float:
        return self.balances.get(address, 0.0)

    def save_state_to_disk(self) -> None:
        """Zrzuca cache pamięci do pliku."""
        with open(self.file_path, "w") as f:
            f.write(JsonSerializer.serialize(self.balances))

    def _load_state_from_disk(self) -> None:
        if not os.path.exists(self.file_path):
            self.balances = {}
            return
            
        try:
            with open(self.file_path, "r") as f:
                content = f.read()
                if content:
                    self.balances = json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            self.balances = {}
