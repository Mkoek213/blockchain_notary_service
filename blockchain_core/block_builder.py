"""
Implementacja klasy Block z wzorcem Builder zgodnie z dokumentacją.
"""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from .crypto_service import ICryptoService
from .notarial_document import NotarialDocument


class Block:
    """
    Reprezentuje pojedynczy blok w blockchain dla serwisu notarialnego.

    Blok może być utworzony TYLKO przez BlockBuilder (wzorzec Builder).

    Atrybuty:
        previous_hash: Hash poprzedniego bloku
        hash: Hash bieżącego bloku
        timestamp: Czas utworzenia bloku
        documents: Lista dokumentów notarialnych
        extra_data: Dodatkowe dane (np. podpis cyfrowy)
        transactions_root: Root hash drzewa Merkle transakcji
        state_root: Root hash stanu blockchain
        miner: Adres minera/autora bloku
    """

    def __init__(self, builder: "BlockBuilder"):
        """
        Konstruktor prywatny - blok może być tworzony tylko przez Builder.

        Args:
            builder: Instancja BlockBuilder z ustawionymi parametrami
        """
        self.previous_hash: str = builder._parent_hash
        self.timestamp: float = builder._timestamp
        self.documents: List[NotarialDocument] = builder._documents.copy()
        self.miner: str = builder._miner_address
        self.transactions_root: str = builder._transactions_root
        self.state_root: str = builder._state_root
        self.extra_data: str = builder._extra_data

        # Hash obliczany po ustawieniu wszystkich pól
        self.hash: str = self.calculate_hash()

    def calculate_hash(self) -> str:
        """
        Oblicza hash SHA-256 bloku na podstawie jego zawartości.

        Returns:
            Hex string reprezentujący hash bloku
        """
        # Konwertuj dokumenty do JSON
        documents_data = [doc.get_json_data() for doc in self.documents]

        block_content = {
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "documents": documents_data,
            "miner": self.miner,
            "transactions_root": self.transactions_root,
            "state_root": self.state_root,
            "extra_data": self.extra_data,
        }

        block_string = json.dumps(block_content, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def get_hash(self) -> str:
        """
        Zwraca hash bloku.

        Returns:
            Hash bloku
        """
        return self.hash

    def get_parent_hash(self) -> str:
        """
        Zwraca hash rodzica (poprzedniego bloku).

        Returns:
            Hash poprzedniego bloku
        """
        return self.previous_hash

    def sign_block(self, private_key: str, crypto_service: ICryptoService) -> None:
        """
        Podpisuje blok kluczem prywatnym.

        Args:
            private_key: Klucz prywatny minera
            crypto_service: Serwis kryptograficzny do podpisywania
        """
        block_data = self._get_signable_data()
        signature = crypto_service.sign_block(block_data, private_key)
        self.extra_data = signature
        # Przelicz hash po dodaniu podpisu
        self.hash = self.calculate_hash()

    def validate_signature(self, public_key: str, crypto_service: ICryptoService) -> bool:
        """
        Waliduje podpis cyfrowy bloku.

        Args:
            public_key: Klucz publiczny minera
            crypto_service: Serwis kryptograficzny do weryfikacji

        Returns:
            True jeśli podpis jest poprawny
        """
        if not self.extra_data:
            return False

        block_data = self._get_signable_data()
        return crypto_service.verify_signature(block_data, self.extra_data, public_key)

    def get_json_data(self) -> str:
        """
        Zwraca reprezentację JSON bloku.

        Returns:
            String JSON reprezentujący blok
        """
        documents_data = [
            doc.to_dict() if hasattr(doc, "to_dict") else doc.get_json_data()
            for doc in self.documents
        ]

        block_data = {
            "hash": self.hash,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "miner": self.miner,
            "documents": documents_data,
            "transactions_root": self.transactions_root,
            "state_root": self.state_root,
            "extra_data": self.extra_data,
        }

        return json.dumps(block_data, sort_keys=True, indent=2)

    def _get_signable_data(self) -> Dict[str, Any]:
        """
        Zwraca dane bloku do podpisania (bez extra_data).

        Returns:
            Słownik z danymi bloku
        """
        documents_data = [doc.get_json_data() for doc in self.documents]

        return {
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "documents": documents_data,
            "miner": self.miner,
            "transactions_root": self.transactions_root,
            "state_root": self.state_root,
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Konwertuje blok do słownika (serializacja).

        Returns:
            Słownik reprezentujący blok
        """
        documents_data = [
            doc.to_dict() if hasattr(doc, "to_dict") else json.loads(doc.get_json_data())
            for doc in self.documents
        ]

        return {
            "hash": self.hash,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "miner": self.miner,
            "documents": documents_data,
            "transactions_root": self.transactions_root,
            "state_root": self.state_root,
            "extra_data": self.extra_data,
        }

    def is_genesis_block(self) -> bool:
        """
        Sprawdza czy blok jest blokiem genesis.

        Returns:
            True jeśli to blok genesis
        """
        return self.previous_hash == "0"

    def __repr__(self) -> str:
        """String reprezentacja bloku."""
        return f"Block(hash={self.hash[:16]}..., miner={self.miner})"

    def __str__(self) -> str:
        """Czytelna string reprezentacja bloku."""
        return f"Block [{self.hash[:10]}...] by {self.miner}"


class BlockBuilder:
    """
    Builder dla klasy Block (wzorzec Builder).

    Umożliwia stopniowe budowanie bloku z walidacją parametrów.
    """

    def __init__(self):
        """Inicjalizuje pusty builder."""
        self._parent_hash: Optional[str] = None
        self._timestamp: float = datetime.now().timestamp()
        self._documents: List[NotarialDocument] = []
        self._miner_address: Optional[str] = None
        self._transactions_root: str = ""
        self._state_root: str = ""
        self._extra_data: str = ""

    def set_parent_hash(self, hash: str) -> "BlockBuilder":
        """
        Ustawia hash poprzedniego bloku.

        Args:
            hash: Hash rodzica

        Returns:
            Self dla method chaining
        """
        self._parent_hash = hash
        return self

    def add_document(self, doc: NotarialDocument) -> "BlockBuilder":
        """
        Dodaje dokument notarialny do bloku.

        Args:
            doc: Dokument notarialny

        Returns:
            Self dla method chaining
        """
        self._documents.append(doc)
        return self

    def set_roots(self, tx_root: str, state_root: str) -> "BlockBuilder":
        """
        Ustawia root hashe dla transakcji i stanu.

        Args:
            tx_root: Transactions root hash
            state_root: State root hash

        Returns:
            Self dla method chaining
        """
        self._transactions_root = tx_root
        self._state_root = state_root
        return self

    def set_timestamp(self, time: float) -> "BlockBuilder":
        """
        Ustawia timestamp bloku.

        Args:
            time: Unix timestamp

        Returns:
            Self dla method chaining
        """
        self._timestamp = time
        return self

    def set_author(self, miner_address: str) -> "BlockBuilder":
        """
        Ustawia adres autora/minera bloku.

        Args:
            miner_address: Adres minera

        Returns:
            Self dla method chaining
        """
        self._miner_address = miner_address
        return self

    def build(
        self, crypto_service: Optional[ICryptoService] = None, private_key: Optional[str] = None
    ) -> Block:
        """
        Buduje blok z ustawionych parametrów.

        Wykonuje następujące kroki:
        1. Waliduje parametry wejściowe
        2. Oblicza root hashe jeśli nie zostały ustawione
        3. Opcjonalnie podpisuje blok
        4. Tworzy i zwraca instancję Block

        Args:
            crypto_service: Opcjonalny serwis do podpisywania
            private_key: Opcjonalny klucz prywatny do podpisania

        Returns:
            Nowa instancja Block

        Raises:
            ValueError: Jeśli wymagane parametry nie zostały ustawione
        """
        # Walidacja parametrów
        self._validate_inputs()

        # Oblicz root hashe jeśli nie zostały ustawione
        self._calculate_roots()

        # Utwórz blok
        block = Block(self)

        # Opcjonalnie podpisz blok
        if crypto_service and private_key:
            block.sign_block(private_key, crypto_service)

        return block

    def _validate_inputs(self) -> None:
        """
        Waliduje czy wszystkie wymagane parametry zostały ustawione.

        Raises:
            ValueError: Jeśli brakuje wymaganych parametrów
        """
        if self._parent_hash is None:
            raise ValueError("Parent hash must be set before building block")

        if self._miner_address is None:
            raise ValueError("Miner address must be set before building block")

        if self._timestamp <= 0:
            raise ValueError("Timestamp must be positive")

    def _calculate_roots(self) -> None:
        """
        Oblicza transactions root i state root jeśli nie zostały ustawione.
        Używa prostego algorytmu hashowania dla dokumentów.
        """
        if not self._transactions_root:
            # Oblicz transactions root z dokumentów
            if self._documents:
                docs_data = [doc.get_json_data() for doc in self._documents]
                combined = "".join(sorted(docs_data))
                self._transactions_root = hashlib.sha256(combined.encode()).hexdigest()
            else:
                self._transactions_root = hashlib.sha256(b"").hexdigest()

        if not self._state_root:
            # State root może być obliczony na podstawie aktualnego stanu
            # Na razie używamy prostego hasha
            state_data = f"{self._parent_hash}{self._timestamp}"
            self._state_root = hashlib.sha256(state_data.encode()).hexdigest()
