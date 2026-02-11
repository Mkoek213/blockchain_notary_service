"""
Moduł walidacji biznesowej dla systemu notarialnego blockchain.

Klasa BusinessLogicModule implementuje interfejs IBusinessLogicModule
z blockchain_core. Odpowiada za walidację transakcji z uwzględnieniem
stanu blockchain (World State), wykrywanie double spending oraz
wykonywanie smart contracts.

Używa wstrzykiwania zależności (DI) dla WorldState.
"""

import hashlib
import json
from typing import Any, Dict

# Dodajemy ścieżkę do blockchain_core
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from blockchain_core import IBusinessLogicModule

from .world_state import SimpleWorldState


class BusinessLogicModule(IBusinessLogicModule):
    """
    Implementacja walidacji biznesowej dla systemu notarialnego.

    Odpowiada na pytanie: 'czy transakcja jest poprawna prawnie i biznesowo?'
    Weryfikuje reguły notarialne (sprzedaż udziałów, głosowanie) przed ich
    trwałym zapisaniem w rejestrze.

    Wykorzystuje Dependency Injection - WorldState jest wstrzykiwany
    przez konstruktor, co umożliwia łatwe testowanie i wymianę implementacji.
    """

    def __init__(self, world_state: SimpleWorldState):
        """
        Inicjalizuje moduł z wstrzykniętym stanem świata.

        Args:
            world_state: Instancja SimpleWorldState do odczytu stanu posiadania
        """
        self._world_state = world_state

    @property
    def world_state(self) -> SimpleWorldState:
        """Zwraca referencję do World State."""
        return self._world_state

    # ========================================================================
    # Implementacja IBusinessLogicModule
    # ========================================================================

    def validate_transaction(
        self, transaction_data: Dict[str, Any], blockchain_state: Any
    ) -> bool:
        """
        Waliduje transakcję z uwzględnieniem stanu blockchain.

        Kolejność sprawdzeń (zgodnie z wymaganiami):
        1. Sprawdzenie double spending
        2. Walidacja specyficzna dla typu transakcji

        Args:
            transaction_data: Dane transakcji do walidacji
            blockchain_state: Aktualny stan blockchain (World State)

        Returns:
            True jeśli transakcja jest poprawna biznesowo
        """
        # 1. Sprawdź double spending
        doc_id = self._compute_document_id(transaction_data)
        if self.check_double_spending(doc_id):
            return False

        # 2. Walidacja specyficzna dla typu
        doc_type = transaction_data.get("type", "")

        if doc_type == "SharesTransfer":
            return self._validate_shares_transfer_data(transaction_data)
        elif doc_type == "Transaction":
            return self._validate_financial_transaction(transaction_data)
        elif doc_type == "CompanyRegistration":
            return self._validate_company_registration(transaction_data)
        elif doc_type == "SharesAllocation":
            return self._validate_shares_allocation(transaction_data)
        elif doc_type == "BalanceUpdate":
            return self._validate_balance_update(transaction_data)
        elif doc_type == "Resolution":
            return self._validate_resolution(transaction_data)
        elif doc_type == "Dividend":
            return self._validate_dividend(transaction_data)

        # Nieznany typ - odrzuć
        return False

    def execute_smart_contract(
        self, contract_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Wykonuje logikę smart contract i zwraca rezultat.

        W kontekście systemu notarialnego, smart contract to zautomatyzowana
        weryfikacja reguł notarialnych (np. sekwencja sprawdzeń z diagramu
        sekwencji: walidacja stanu konta → walidacja posiadanych akcji →
        zatwierdzenie operacji).

        Args:
            contract_data: Dane kontraktu do wykonania

        Returns:
            Rezultat wykonania kontraktu ze statusem i szczegółami
        """
        contract_type = contract_data.get("contract_type", "")

        if contract_type == "shares_transfer":
            return self._execute_shares_transfer_contract(contract_data)
        elif contract_type == "dividend_payout":
            return self._execute_dividend_contract(contract_data)

        return {
            "status": "rejected",
            "reason": f"Nieznany typ kontraktu: {contract_type}",
        }

    def check_double_spending(self, document_id: str) -> bool:
        """
        Sprawdza czy dokument o danym ID został już przetworzony.

        Zapobiega wielokrotnemu zatwierdzeniu tej samej transakcji.

        Args:
            document_id: Identyfikator (hash) dokumentu

        Returns:
            True jeśli dokument już istnieje (= double spending wykryty)
        """
        return self._world_state.has_document(document_id)

    def validate_shares_transfer(
        self, sender: str, recipient: str, shares: int, company_id: str
    ) -> bool:
        """
        Waliduje transfer udziałów w spółce.

        Sprawdza:
        1. Czy spółka istnieje
        2. Czy sprzedający posiada wystarczającą liczbę udziałów
        3. Czy liczba udziałów jest dodatnia
        4. Czy nadawca i odbiorca to różne osoby

        Args:
            sender: ID właściciela udziałów (sprzedający)
            recipient: ID nabywcy (kupujący)
            shares: Liczba udziałów do przeniesienia
            company_id: ID spółki

        Returns:
            True jeśli transfer jest możliwy
        """
        # Walidacja podstawowa
        if shares <= 0:
            return False

        if sender == recipient:
            return False

        # Sprawdź czy spółka istnieje
        company = self._world_state.get_company(company_id)
        if not company:
            return False

        # Sprawdź czy sprzedający ma wystarczającą liczbę udziałów
        current_shares = self._world_state.get_shares(sender, company_id)
        if current_shares < shares:
            return False

        return True

    # ========================================================================
    # Prywatne metody walidacji
    # ========================================================================

    def _validate_shares_transfer_data(self, data: Dict[str, Any]) -> bool:
        """Waliduje dane transferu udziałów z transaction_data dict."""
        required = ["seller", "buyer", "company_id", "shares_count"]
        if not all(f in data for f in required):
            return False

        return self.validate_shares_transfer(
            sender=data["seller"],
            recipient=data["buyer"],
            shares=data["shares_count"],
            company_id=data["company_id"],
        )

    def _validate_financial_transaction(self, data: Dict[str, Any]) -> bool:
        """
        Waliduje transakcję finansową.

        Sprawdza czy nadawca ma wystarczające saldo.
        """
        required = ["sender", "recipient", "amount"]
        if not all(f in data for f in required):
            return False

        amount = data["amount"]
        if amount <= 0:
            return False

        sender = data["sender"]
        balance = self._world_state.get_balance(sender)

        if balance < amount:
            return False

        return True

    def _validate_company_registration(self, data: Dict[str, Any]) -> bool:
        company_id = data.get("company_id")
        if not company_id:
            return False
        existing = self._world_state.get_company(company_id)
        return existing is None

    def _validate_shares_allocation(self, data: Dict[str, Any]) -> bool:
        if not data.get("account_id") or not data.get("company_id"):
            return False
        shares = data.get("shares")
        if not isinstance(shares, int):
            return False
        return shares >= 0

    def _validate_balance_update(self, data: Dict[str, Any]) -> bool:
        if not data.get("account_id"):
            return False
        balance = data.get("balance")
        if not isinstance(balance, (int, float)):
            return False
        return True

    def _validate_resolution(self, data: Dict[str, Any]) -> bool:
        """
        Waliduje uchwałę/głosowanie.

        Sprawdza czy dane są kompletne i spółka istnieje.
        """
        required = ["resolution_id", "company_id", "votes_for", "votes_against"]
        if not all(f in data for f in required):
            return False

        # Sprawdź czy spółka istnieje
        company = self._world_state.get_company(data["company_id"])
        if not company:
            return False

        return True

    def _validate_dividend(self, data: Dict[str, Any]) -> bool:
        """
        Waliduje wypłatę dywidendy.

        Sprawdza czy dane są kompletne i spółka istnieje.
        """
        required = ["company_id", "amount_per_share", "total_amount"]
        if not all(f in data for f in required):
            return False

        if data["amount_per_share"] <= 0 or data["total_amount"] <= 0:
            return False

        company = self._world_state.get_company(data["company_id"])
        if not company:
            return False

        return True

    # ========================================================================
    # Smart contract execution
    # ========================================================================

    def _execute_shares_transfer_contract(
        self, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Wykonuje smart contract transferu udziałów.

        Sekwencja zgodnie z diagramem z dokumentacji:
        1. Walidacja stanu konta
        2. Walidacja posiadanych akcji
        3. Zatwierdzenie lub odrzucenie operacji
        """
        seller = data.get("seller", "")
        buyer = data.get("buyer", "")
        company_id = data.get("company_id", "")
        shares_count = data.get("shares_count", 0)

        # Krok 1: Walidacja posiadanych akcji
        is_valid = self.validate_shares_transfer(
            sender=seller,
            recipient=buyer,
            shares=shares_count,
            company_id=company_id,
        )

        if not is_valid:
            current_shares = self._world_state.get_shares(seller, company_id)
            return {
                "status": "rejected",
                "reason": f"{seller} posiada {current_shares} udziałów, "
                          f"potrzeba {shares_count}",
                "seller": seller,
                "buyer": buyer,
                "company_id": company_id,
            }

        # Krok 2: Zatwierdzenie
        return {
            "status": "approved",
            "seller": seller,
            "buyer": buyer,
            "company_id": company_id,
            "shares_count": shares_count,
        }

    def _execute_dividend_contract(
        self, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Wykonuje smart contract wypłaty dywidendy."""
        company_id = data.get("company_id", "")
        amount_per_share = data.get("amount_per_share", 0)

        company = self._world_state.get_company(company_id)
        if not company:
            return {
                "status": "rejected",
                "reason": f"Spółka {company_id} nie istnieje",
            }

        return {
            "status": "approved",
            "company_id": company_id,
            "amount_per_share": amount_per_share,
        }

    # ========================================================================
    # Metody pomocnicze
    # ========================================================================

    def _compute_document_id(self, data: Dict[str, Any]) -> str:
        """
        Oblicza unikalny identyfikator dokumentu (hash).

        Args:
            data: Dane dokumentu

        Returns:
            Hash SHA-256 jako string hex
        """
        # Usuwamy podpisy - nie wpływają na tożsamość dokumentu
        data_copy = {k: v for k, v in data.items() if k != "signatures"}
        data_str = json.dumps(data_copy, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
