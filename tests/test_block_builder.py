"""
Testy jednostkowe dla BlockBuilder i Block.
Testujemy wzorzec Builder i wszystkie metody klasy Block.
"""

import time

import pytest

from blockchain_core import BlockBuilder, Transaction, VotingResult
from blockchain_core.mock_crypto import MockCryptoService


class TestBlockBuilder:
    """Testy dla wzorca Builder - sprawdzamy poprawność budowania bloków."""

    def setup_method(self):
        """Przygotowanie przed każdym testem."""
        self.crypto_service = MockCryptoService()
        self.pub_key, self.priv_key = self.crypto_service.generate_key_pair()
        self.builder = BlockBuilder()

    def test_builder_creates_valid_block(self):
        """Test tworzenia poprawnego bloku."""
        # Given
        parent_hash = "genesis_hash"
        transaction = Transaction("Alice", "Bob", 100.0)

        # When
        block = (
            self.builder.set_parent_hash(parent_hash)
            .set_author("miner_1")
            .add_document(transaction)
            .build(self.crypto_service, self.priv_key)
        )

        # Then
        assert block is not None
        assert block.get_parent_hash() == parent_hash
        assert block.miner == "miner_1"
        assert len(block.documents) == 1
        assert block.get_hash() is not None

    def test_builder_validates_missing_parent_hash(self):
        """Test walidacji braku parent_hash."""
        # Given
        transaction = Transaction("Alice", "Bob", 100.0)

        # When/Then
        with pytest.raises(ValueError, match="Parent hash must be set before building block"):
            self.builder.set_author("miner_1").add_document(transaction).build(
                self.crypto_service, self.priv_key
            )

    def test_builder_validates_missing_author(self):
        """Test walidacji braku autora."""
        # Given
        transaction = Transaction("Alice", "Bob", 100.0)

        # When/Then
        with pytest.raises(ValueError, match="Miner address must be set before building block"):
            self.builder.set_parent_hash("genesis_hash").add_document(transaction).build(
                self.crypto_service, self.priv_key
            )

    def test_builder_adds_multiple_documents(self):
        """Test dodawania wielu dokumentów."""
        # Given
        transaction = Transaction("Alice", "Bob", 100.0)
        voting = VotingResult("VOTE-001", {"Yes": 10, "No": 5})

        # When
        block = (
            self.builder.set_parent_hash("genesis_hash")
            .set_author("miner_1")
            .add_document(transaction)
            .add_document(voting)
            .build(self.crypto_service, self.priv_key)
        )

        # Then
        assert len(block.documents) == 2
        assert block.documents[0] == transaction
        assert block.documents[1] == voting

    def test_block_signature_validation(self):
        """Test walidacji podpisu bloku."""
        # Given
        transaction = Transaction("Alice", "Bob", 100.0)
        block = (
            self.builder.set_parent_hash("genesis_hash")
            .set_author("miner_1")
            .add_document(transaction)
            .build(self.crypto_service, self.priv_key)
        )

        # When
        is_valid = block.validate_signature(self.pub_key, self.crypto_service)

        # Then
        assert is_valid is True

    def test_block_signature_invalid_with_wrong_key(self):
        """Test walidacji podpisu z niewłaściwym kluczem."""
        # Given
        transaction = Transaction("Alice", "Bob", 100.0)
        block = (
            self.builder.set_parent_hash("genesis_hash")
            .set_author("miner_1")
            .add_document(transaction)
            .build(self.crypto_service, self.priv_key)
        )

        # Other key
        other_pub_key, _ = self.crypto_service.generate_key_pair()

        # When
        is_valid = block.validate_signature(other_pub_key, self.crypto_service)

        # Then
        assert is_valid is False

    def test_block_has_timestamp(self):
        """Test czy blok ma timestamp."""
        # Given/When
        block = (
            self.builder.set_parent_hash("genesis_hash")
            .set_author("miner_1")
            .add_document(Transaction("Alice", "Bob", 100.0))
            .build(self.crypto_service, self.priv_key)
        )

        # Then
        assert block.timestamp > 0

    def test_block_calculates_transactions_root(self):
        """Test obliczania transactions_root."""
        # Given/When
        block = (
            self.builder.set_parent_hash("genesis_hash")
            .set_author("miner_1")
            .add_document(Transaction("Alice", "Bob", 100.0))
            .build(self.crypto_service, self.priv_key)
        )

        # Then
        assert block.transactions_root is not None
        assert len(block.transactions_root) > 0

    def test_block_to_dict(self):
        """Test konwersji bloku do słownika."""
        # Given/When
        block = (
            self.builder.set_parent_hash("genesis_hash")
            .set_author("miner_1")
            .add_document(Transaction("Alice", "Bob", 100.0))
            .build(self.crypto_service, self.priv_key)
        )

        block_dict = block.to_dict()

        # Then
        assert "hash" in block_dict
        assert "previous_hash" in block_dict
        assert "miner" in block_dict
        assert "documents" in block_dict
        assert block_dict["miner"] == "miner_1"

    def test_block_get_json_data(self):
        """Test eksportu bloku do JSON."""
        # Given
        block = (
            self.builder.set_parent_hash("genesis_hash")
            .set_author("miner_1")
            .add_document(Transaction("Alice", "Bob", 100.0))
            .build(self.crypto_service, self.priv_key)
        )

        # When
        json_data = block.get_json_data()

        # Then
        assert isinstance(json_data, str)
        assert "miner_1" in json_data
        assert "Alice" in json_data

    def test_block_state_root_calculation(self):
        """Test obliczania state_root."""
        # Given/When
        block = (
            self.builder.set_parent_hash("genesis_hash")
            .set_author("miner_1")
            .add_document(Transaction("Alice", "Bob", 100.0))
            .build(self.crypto_service, self.priv_key)
        )

        # Then
        assert block.state_root is not None
        assert len(block.state_root) > 0

    def test_block_extra_data_contains_signature(self):
        """Test czy extra_data zawiera podpis."""
        # Given/When
        block = (
            self.builder.set_parent_hash("genesis_hash")
            .set_author("miner_1")
            .add_document(Transaction("Alice", "Bob", 100.0))
            .build(self.crypto_service, self.priv_key)
        )

        # Then
        assert block.extra_data is not None
        assert len(block.extra_data) > 0

    def test_block_hash_changes_with_content(self):
        """Test czy hash bloku zmienia się wraz z zawartością."""
        # Given
        block1 = (
            BlockBuilder()
            .set_parent_hash("genesis_hash")
            .set_author("miner_1")
            .add_document(Transaction("Alice", "Bob", 100.0))
            .build(self.crypto_service, self.priv_key)
        )

        time.sleep(0.01)  # Różny timestamp

        block2 = (
            BlockBuilder()
            .set_parent_hash("genesis_hash")
            .set_author("miner_1")
            .add_document(Transaction("Alice", "Bob", 100.0))
            .build(self.crypto_service, self.priv_key)
        )

        # Then
        assert block1.get_hash() != block2.get_hash()

    def test_builder_fluent_interface(self):
        """Test interfejsu fluent (łańcuchowe wywołania)."""
        # Given/When
        result = (
            self.builder.set_parent_hash("genesis_hash")
            .set_author("miner_1")
            .add_document(Transaction("Alice", "Bob", 100.0))
        )

        # Then - każda metoda zwraca builder
        assert result == self.builder

    def test_block_immutability_no_setters(self):
        """Test niezmienności bloku - brak publicznych setterów."""
        # Given
        block = (
            self.builder.set_parent_hash("genesis_hash")
            .set_author("miner_1")
            .add_document(Transaction("Alice", "Bob", 100.0))
            .build(self.crypto_service, self.priv_key)
        )

        # Then - próba zmiany pól powinna być niemożliwa poprzez publiczne API
        assert not hasattr(block, "set_hash")
        assert not hasattr(block, "set_miner")

    def test_block_documents_are_preserved(self):
        """Test czy dokumenty są prawidłowo zachowane w bloku."""
        # Given
        doc1 = Transaction("Alice", "Bob", 100.0)
        doc2 = VotingResult("VOTE-001", {"Yes": 10, "No": 5})

        # When
        block = (
            self.builder.set_parent_hash("genesis_hash")
            .set_author("miner_1")
            .add_document(doc1)
            .add_document(doc2)
            .build(self.crypto_service, self.priv_key)
        )

        # Then
        assert len(block.documents) == 2
        assert block.documents[0].sender == "Alice"
        assert block.documents[1].voting_id == "VOTE-001"
