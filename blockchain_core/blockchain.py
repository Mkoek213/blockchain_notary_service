"""
Implementacja klasy Blockchain - głównego komponentu zarządzającego łańcuchem bloków.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .block_builder import Block, BlockBuilder
from .crypto_service import ICryptoService
from .interfaces import IBlockchainInterface, INotaryValidator, IStorageProvider


class Blockchain(IBlockchainInterface):
    """
    Główna klasa zarządzająca blockchain dla serwisu notarialnego.

    Odpowiada za:
    - Tworzenie i zarządzanie łańcuchem bloków
    - Walidację bloków i łańcucha
    - Integrację z modułami zewnętrznymi (storage, consensus, validation)
    - Dodawanie dokumentów notarialnych
    """

    def __init__(
        self,
        storage_provider: Optional[IStorageProvider] = None,
        notary_validator: Optional[INotaryValidator] = None,
        crypto_service: Optional[ICryptoService] = None,
    ):
        """
        Inicjalizuje blockchain.

        Args:
            storage_provider: Provider do przechowywania danych
            storage_provider: Provider do przechowywania danych
            notary_validator: Validator dokumentów notarialnych
            crypto_service: Serwis kryptograficzny do podpisywania bloków
        """
        self.chain: List[Block] = []
        self.pending_data: List[Dict[str, Any]] = []

        # Opcjonalne moduły zewnętrzne
        self.storage_provider = storage_provider
        self.notary_validator = notary_validator
        self.crypto_service = crypto_service

        # Inicjalizacja łańcucha
        self._initialize_chain()

    def _initialize_chain(self) -> None:
        """
        Inicjalizuje łańcuch bloków.

        Próbuje wczytać z storage, jeśli nie istnieje - tworzy blok genesis.
        """
        # Spróbuj wczytać z storage
        if self.storage_provider:
            loaded_chain = self.storage_provider.load_blockchain()
            if loaded_chain:
                # TODO: Zaimplementuj deserializację dla nowego formatu Block
                # self.chain = [Block.from_dict(block_data) for block_data in loaded_chain]
                pass

        # Jeśli nie udało się wczytać, utwórz blok genesis
        self._create_genesis_block()

    def _create_genesis_block(self) -> None:
        """Tworzy pierwszy blok (genesis) w łańcuchu używając BlockBuilder."""
        # Użyj BlockBuilder do utworzenia bloku genesis
        builder = BlockBuilder()
        genesis_block = (
            builder.set_parent_hash("0")
            .set_author("genesis")
            .set_timestamp(1.0)
            .build()
        )

        self.chain.append(genesis_block)

        # Zapisz do storage jeśli dostępny
        if self.storage_provider:
            self.storage_provider.save_block(genesis_block.to_dict())

    def get_latest_block(self) -> Block:
        """
        Pobiera ostatni blok w łańcuchu.

        Returns:
            Ostatni blok w łańcuchu
        """
        return self.chain[-1]

    def get_last_block(self) -> Block:
        """
        Alias dla get_latest_block() - zgodnie z diagramem sekwencji.
        Pobiera ostatni blok w łańcuchu.

        Returns:
            Ostatni blok w łańcuchu
        """
        return self.get_latest_block()

    def get_height(self) -> int:
        """
        Zwraca wysokość łańcucha (liczbę bloków).
        Potrzebne dla modułu Network do synchronizacji.

        Returns:
            Wysokość łańcucha (liczba bloków)
        """
        return len(self.chain)

    def get_blocks_range(self, start_height: int, end_height: int) -> List[Block]:
        """
        Zwraca zakres bloków dla synchronizacji z innymi węzłami.
        Potrzebne dla modułu Network.

        Args:
            start_height: Początkowa wysokość (inclusive)
            end_height: Końcowa wysokość (inclusive)

        Returns:
            Lista bloków w zadanym zakresie
        """
        if start_height < 0 or end_height >= len(self.chain):
            return []

        if start_height > end_height:
            return []

        return self.chain[start_height : end_height + 1]

    def validate_and_add_block(self, block: Block) -> bool:
        """
        Waliduje i dodaje blok otrzymany z sieci.
        Potrzebne dla modułu Network.

        Args:
            block: Blok otrzymany z sieci

        Returns:
            True jeśli blok został zaakceptowany i dodany
        """
        return self.append_block(block)

    def append_block(self, block: Block) -> bool:
        """
        Dodaje gotowy blok do łańcucha (zgodnie z diagramem sekwencji).
        Waliduje blok przed dodaniem.

        Args:
            block: Blok do dodania

        Returns:
            True jeśli blok został dodany pomyślnie
        """
        if not self.chain:
            return False

        previous_block = self.get_latest_block()

        # Waliduj blok
        if block.get_parent_hash() != previous_block.get_hash():
            return False

        # Dodaj do łańcucha
        self.chain.append(block)

        # Zapisz do storage jeśli dostępny
        if self.storage_provider:
            self.storage_provider.save_block(block.to_dict())

        return True

    def validate_chain(self) -> bool:
        """
        Waliduje cały łańcuch bloków.

        Returns:
            True jeśli cały łańcuch jest poprawny
        """
        # Sprawdź blok genesis
        if not self.chain[0].is_genesis_block():
            return False

        # Waliduj każdy blok względem poprzedniego
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Podstawowa walidacja parent hash
            if current_block.get_parent_hash() != previous_block.get_hash():
                return False

        return True

    def to_dict(self) -> List[Dict[str, Any]]:
        """
        Konwertuje cały blockchain do listy słowników.

        Returns:
            Lista bloków jako słowniki
        """
        return [block.to_dict() for block in self.chain]

    def __len__(self) -> int:
        """Zwraca liczbę bloków w łańcuchu."""
        return len(self.chain)

    def __repr__(self) -> str:
        """String reprezentacja blockchain."""
        return f"Blockchain(blocks={len(self.chain)})"

    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        """
        Znajduje blok po jego hashu w lokalnym łańcuchu.

        Args:
            block_hash: Hash bloku

        Returns:
            Blok lub None jeśli nie znaleziono
        """
        for block in self.chain:
            if block.hash == block_hash:
                return block
        return None

    def get_chain_stats(self) -> Dict[str, Any]:
        """
        Pobiera statystyki blockchain.

        Returns:
            Słownik ze statystykami
        """
        return {
            "total_blocks": len(self.chain),
            "latest_block_hash": self.get_latest_block().get_hash(),
            "is_valid": self.validate_chain(),
        }

    # ========================================================================
    # Dodatkowe metody IBlockchainInterface - zgodnie z wymaganiami
    # ========================================================================

    def get_latest_block_hash(self) -> str:
        """
        Zwraca hash ostatniego bloku w łańcuchu.
        Potrzebne dla modułu Network.

        Returns:
            Hash ostatniego bloku
        """
        return self.get_latest_block().get_hash()

    def has_block(self, hash: str) -> bool:
        """
        Sprawdza czy blok o podanym hashu istnieje w łańcuchu.
        Potrzebne dla modułu Network do weryfikacji bloków.

        Args:
            hash: Hash bloku do sprawdzenia

        Returns:
            True jeśli blok istnieje, False w przeciwnym razie
        """
        return self.get_block_by_hash(hash) is not None

    def handle_transactions(self, tx_data: dict) -> None:
        """
        Obsługuje przychodzącą transakcję z sieci.
        Dodaje do puli oczekujących transakcji (pending_data).
        Potrzebne dla modułu Network.

        Args:
            tx_data: Dane transakcji do przetworzenia
        """
        # Walidacja transakcji jeśli dostępny validator
        if self.notary_validator:
            if not self.notary_validator.validate_document(tx_data):
                return

        # Dodaj do puli oczekujących
        self.pending_data.append(tx_data)

    def get_blocks_from(self, height: int) -> List[Block]:
        """
        Zwraca wszystkie bloki od podanej wysokości do końca łańcucha.
        Potrzebne dla modułu Network do synchronizacji.

        Args:
            height: Początkowa wysokość (inclusive)

        Returns:
            Lista bloków od height do końca łańcucha
        """
        if height < 0 or height >= len(self.chain):
            return []

        return self.chain[height:]
