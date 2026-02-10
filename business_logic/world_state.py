"""
World State - aktualny stan posiadania odtworzony z łańcucha bloków.

Klasa SimpleWorldState skanuje historię bloków i na tej podstawie
oblicza bieżące salda kont oraz stan posiadania udziałów w spółkach.
Służy jako źródło danych dla walidacji biznesowej (BusinessLogicModule).
"""

import json
from typing import Any, Dict, Optional, Set, Tuple

# Dodajemy ścieżkę do blockchain_core
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class SimpleWorldState:
    """
    In-memory World State budowany z rzeczywistego łańcucha bloków.

    Skanuje dokumenty ze wszystkich bloków i na ich podstawie oblicza:
    - salda kont (z transakcji finansowych)
    - stan posiadania udziałów (z transferów udziałów)
    - zbiór przetworzonych dokumentów (do wykrywania double spending)

    Pełna implementacja IWorldStateManager z persystencją należy
    do modułu Storage (Moduł 5).
    """

    def __init__(self):
        """Inicjalizuje pusty stan świata."""
        # Salda kont: account_id -> balance
        self._balances: Dict[str, float] = {}

        # Posiadane udziały: (account_id, company_id) -> shares_count
        self._shares: Dict[Tuple[str, str], int] = {}

        # Zarejestrowane spółki: company_id -> info dict
        self._companies: Dict[str, Dict[str, Any]] = {}

        # IDs przetworzonych dokumentów (do double-spending check)
        self._processed_documents: Set[str] = set()

    # ========================================================================
    # Budowanie stanu z blockchaina
    # ========================================================================

    def build_from_blockchain(self, blockchain) -> None:
        """
        Odtwarza stan świata z historii bloków w łańcuchu.

        Iteruje po wszystkich blokach (z pominięciem genesis),
        analizuje dokumenty i aktualizuje stan posiadania.

        Args:
            blockchain: Instancja Blockchain z blockchain_core
        """
        # Resetuj stan
        self._balances.clear()
        self._shares.clear()
        self._processed_documents.clear()

        # Iteruj po blokach (pomijamy genesis - indeks 0)
        for block in blockchain.chain[1:]:
            self._process_block(block)

    def _process_block(self, block) -> None:
        """
        Przetwarza pojedynczy blok i aktualizuje stan.

        Args:
            block: Instancja Block z blockchain_core
        """
        for document in block.documents:
            doc_data = self._extract_document_data(document)
            if doc_data is None:
                continue

            doc_type = doc_data.get("type", "")

            # Generuj unikalny ID dokumentu dla double-spending check
            doc_id = self._generate_document_id(doc_data)
            self._processed_documents.add(doc_id)

            # Przetwarzaj w zależności od typu dokumentu
            if doc_type == "SharesTransfer":
                self._apply_shares_transfer(doc_data)
            elif doc_type == "Transaction":
                self._apply_transaction(doc_data)
            elif doc_type == "Dividend":
                self._apply_dividend(doc_data)

    def _extract_document_data(self, document) -> Optional[Dict[str, Any]]:
        """
        Wyciąga dane z dokumentu jako słownik.

        Args:
            document: Instancja NotarialDocument

        Returns:
            Słownik z danymi dokumentu lub None
        """
        try:
            if hasattr(document, "to_dict"):
                return document.to_dict()
            else:
                return json.loads(document.get_json_data())
        except (json.JSONDecodeError, AttributeError):
            return None

    def _generate_document_id(self, doc_data: Dict[str, Any]) -> str:
        """
        Generuje unikalny ID dokumentu na podstawie jego danych.

        Args:
            doc_data: Dane dokumentu

        Returns:
            Unikalny identyfikator dokumentu
        """
        import hashlib

        # Usuwamy podpisy - nie wpływają na identyfikację dokumentu
        data_copy = {k: v for k, v in doc_data.items() if k != "signatures"}
        data_str = json.dumps(data_copy, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    # ========================================================================
    # Aplikowanie zmian stanu
    # ========================================================================

    def _apply_shares_transfer(self, data: Dict[str, Any]) -> None:
        """
        Aplikuje transfer udziałów do stanu świata.

        Odejmuje udziały od sprzedającego i dodaje do kupującego.
        """
        seller = data["seller"]
        buyer = data["buyer"]
        company_id = data["company_id"]
        shares_count = data["shares_count"]

        # Odejmij od sprzedającego
        seller_key = (seller, company_id)
        current_seller_shares = self._shares.get(seller_key, 0)
        self._shares[seller_key] = current_seller_shares - shares_count

        # Dodaj do kupującego
        buyer_key = (buyer, company_id)
        current_buyer_shares = self._shares.get(buyer_key, 0)
        self._shares[buyer_key] = current_buyer_shares + shares_count

        # Aktualizuj salda (jeśli jest cena)
        price = data.get("price_per_share", 0)
        if price > 0:
            total_cost = shares_count * price
            self._balances[seller] = self._balances.get(seller, 0) + total_cost
            self._balances[buyer] = self._balances.get(buyer, 0) - total_cost

        # Zarejestruj spółkę jeśli nie istnieje
        if company_id not in self._companies:
            self._companies[company_id] = {"id": company_id}

    def _apply_transaction(self, data: Dict[str, Any]) -> None:
        """
        Aplikuje transakcję finansową do stanu świata.

        Odejmuje kwotę od nadawcy i dodaje do odbiorcy.
        """
        sender = data["sender"]
        recipient = data["recipient"]
        amount = data["amount"]

        self._balances[sender] = self._balances.get(sender, 0) - amount
        self._balances[recipient] = self._balances.get(recipient, 0) + amount

    def _apply_dividend(self, data: Dict[str, Any]) -> None:
        """
        Aplikuje wypłatę dywidendy.

        Znajduje wszystkich udziałowców danej spółki i wypłaca im dywidendę
        proporcjonalnie do posiadanych udziałów.
        """
        company_id = data["company_id"]
        amount_per_share = data["amount_per_share"]

        # Znajdź wszystkich udziałowców tej spółki
        for (account_id, comp_id), shares in self._shares.items():
            if comp_id == company_id and shares > 0:
                payout = shares * amount_per_share
                self._balances[account_id] = self._balances.get(account_id, 0) + payout

    # ========================================================================
    # Odczyt stanu (używane przez BusinessLogicModule)
    # ========================================================================

    def get_balance(self, account_id: str) -> float:
        """
        Zwraca saldo konta.

        Args:
            account_id: Identyfikator konta

        Returns:
            Saldo konta (0.0 jeśli konto nie istnieje)
        """
        return self._balances.get(account_id, 0.0)

    def get_shares(self, account_id: str, company_id: str) -> int:
        """
        Zwraca liczbę udziałów w spółce.

        Args:
            account_id: ID właściciela
            company_id: ID spółki

        Returns:
            Liczba udziałów (0 jeśli brak)
        """
        return self._shares.get((account_id, company_id), 0)

    def get_company(self, company_id: str) -> Optional[Dict[str, Any]]:
        """
        Zwraca informacje o spółce.

        Args:
            company_id: ID spółki

        Returns:
            Słownik z danymi spółki lub None
        """
        return self._companies.get(company_id)

    def has_document(self, document_id: str) -> bool:
        """
        Sprawdza czy dokument o danym ID był już przetworzony.
        Używane do wykrywania double spending.

        Args:
            document_id: Hash/ID dokumentu

        Returns:
            True jeśli dokument już istnieje w historii
        """
        return document_id in self._processed_documents

    # ========================================================================
    # Metody pomocnicze do ręcznego ustawiania stanu (np. w testach)
    # ========================================================================

    def set_shares(self, account_id: str, company_id: str, count: int) -> None:
        """Ręcznie ustawia liczbę udziałów (przydatne do inicjalizacji/testów)."""
        self._shares[(account_id, company_id)] = count

    def set_balance(self, account_id: str, balance: float) -> None:
        """Ręcznie ustawia saldo konta (przydatne do inicjalizacji/testów)."""
        self._balances[account_id] = balance

    def register_company(self, company_id: str, name: str = "") -> None:
        """Rejestruje spółkę w stanie świata."""
        self._companies[company_id] = {"id": company_id, "name": name}

    def register_document(self, document_id: str) -> None:
        """Rejestruje dokument jako przetworzony."""
        self._processed_documents.add(document_id)
