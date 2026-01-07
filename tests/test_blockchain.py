"""
Testy jednostkowe dla Blockchain.
Testujemy zarządzanie łańcuchem bloków, walidację i wszystkie metody publiczne.
"""

from blockchain_core import BlockBuilder, Blockchain, Transaction, VotingResult
from blockchain_core.mock_crypto import MockCryptoService


class TestBlockchain:
    """Testy dla klasy Blockchain - pełna funkcjonalność zarządzania łańcuchem."""

    def setup_method(self):
        """Przygotowanie przed każdym testem."""
        self.blockchain = Blockchain()
        self.crypto_service = MockCryptoService()
        self.pub_key, self.priv_key = self.crypto_service.generate_key_pair()

    def test_blockchain_initializes_with_genesis_block(self):
        """Test inicjalizacji z blokiem genesis."""
        # Then
        assert len(self.blockchain.chain) == 1
        assert self.blockchain.get_height() == 1

        genesis = self.blockchain.get_last_block()
        assert genesis.get_parent_hash() == "0"

    def test_append_valid_block(self):
        """Test dodawania poprawnego bloku."""
        # Given
        parent_hash = self.blockchain.get_last_block().get_hash()
        block = (
            BlockBuilder()
            .set_parent_hash(parent_hash)
            .set_author("miner_1")
            .add_document(Transaction("Alice", "Bob", 100.0))
            .build(self.crypto_service, self.priv_key)
        )

        # When
        success = self.blockchain.append_block(block)

        # Then
        assert success is True
        assert self.blockchain.get_height() == 2
        assert self.blockchain.get_last_block() == block

    def test_append_block_with_invalid_parent_hash(self):
        """Test odrzucenia bloku z niewłaściwym parent_hash."""
        # Given
        block = (
            BlockBuilder()
            .set_parent_hash("invalid_hash")
            .set_author("miner_1")
            .add_document(Transaction("Alice", "Bob", 100.0))
            .build(self.crypto_service, self.priv_key)
        )

        # When
        success = self.blockchain.append_block(block)

        # Then
        assert success is False
        assert self.blockchain.get_height() == 1  # Tylko genesis

    def test_get_blocks_range(self):
        """Test pobierania zakresu bloków."""
        # Given - dodaj 3 bloki
        for i in range(3):
            parent_hash = self.blockchain.get_last_block().get_hash()
            block = (
                BlockBuilder()
                .set_parent_hash(parent_hash)
                .set_author(f"miner_{i}")
                .add_document(Transaction(f"User{i}", f"User{i+1}", 100.0))
                .build(self.crypto_service, self.priv_key)
            )
            self.blockchain.append_block(block)

        # When
        blocks = self.blockchain.get_blocks_range(1, 3)

        # Then
        assert len(blocks) == 3  # Bloki 1, 2, 3 (inclusive range)

    def test_validate_chain(self):
        """Test walidacji poprawnego łańcucha."""
        # Given - dodaj kilka bloków
        for i in range(3):
            parent_hash = self.blockchain.get_last_block().get_hash()
            block = (
                BlockBuilder()
                .set_parent_hash(parent_hash)
                .set_author(f"miner_{i}")
                .add_document(Transaction(f"User{i}", f"User{i+1}", 100.0))
                .build(self.crypto_service, self.priv_key)
            )
            self.blockchain.append_block(block)

        # When
        is_valid = self.blockchain.validate_chain()

        # Then
        assert is_valid is True

    def test_blockchain_height_increases(self):
        """Test zwiększania wysokości łańcucha."""
        # Given
        initial_height = self.blockchain.get_height()

        # When - dodaj 5 bloków
        for i in range(5):
            parent_hash = self.blockchain.get_last_block().get_hash()
            block = (
                BlockBuilder()
                .set_parent_hash(parent_hash)
                .set_author(f"miner_{i}")
                .add_document(Transaction(f"User{i}", f"User{i+1}", 100.0))
                .build(self.crypto_service, self.priv_key)
            )
            self.blockchain.append_block(block)

        # Then
        assert self.blockchain.get_height() == initial_height + 5

    def test_get_last_block_returns_newest(self):
        """Test zwracania ostatniego bloku."""
        # Given - dodaj blok
        parent_hash = self.blockchain.get_last_block().get_hash()
        new_block = (
            BlockBuilder()
            .set_parent_hash(parent_hash)
            .set_author("miner_1")
            .add_document(Transaction("Alice", "Bob", 100.0))
            .build(self.crypto_service, self.priv_key)
        )
        self.blockchain.append_block(new_block)

        # When
        last_block = self.blockchain.get_last_block()

        # Then
        assert last_block == new_block
        assert last_block.miner == "miner_1"

    def test_blockchain_chain_continuity(self):
        """Test ciągłości łańcucha - każdy blok wskazuje na poprzedni."""
        # Given - dodaj 5 bloków
        for i in range(5):
            parent_hash = self.blockchain.get_last_block().get_hash()
            block = (
                BlockBuilder()
                .set_parent_hash(parent_hash)
                .set_author(f"miner_{i}")
                .add_document(Transaction(f"User{i}", f"User{i+1}", 100.0))
                .build(self.crypto_service, self.priv_key)
            )
            self.blockchain.append_block(block)

        # When/Then - sprawdź ciągłość
        for i in range(1, len(self.blockchain.chain)):
            current_block = self.blockchain.chain[i]
            previous_block = self.blockchain.chain[i - 1]
            assert current_block.get_parent_hash() == previous_block.get_hash()

    def test_genesis_block_properties(self):
        """Test właściwości bloku genesis."""
        # Given/When
        genesis = self.blockchain.chain[0]

        # Then
        assert genesis.get_parent_hash() == "0"
        assert genesis.miner == "genesis"
        assert len(genesis.documents) == 0

    def test_append_block_with_documents(self):
        """Test dodawania bloku z wieloma dokumentami."""
        # Given
        parent_hash = self.blockchain.get_last_block().get_hash()
        transaction = Transaction("Alice", "Bob", 100.0)
        voting = VotingResult("VOTE-001", {"Yes": 10, "No": 5})

        block = (
            BlockBuilder()
            .set_parent_hash(parent_hash)
            .set_author("miner_1")
            .add_document(transaction)
            .add_document(voting)
            .build(self.crypto_service, self.priv_key)
        )

        # When
        success = self.blockchain.append_block(block)

        # Then
        assert success is True
        last_block = self.blockchain.get_last_block()
        assert len(last_block.documents) == 2

    def test_get_blocks_range_returns_blocks(self):
        """Test pobierania bloków - upewniamy się że metoda działa."""
        # Given - dodaj 3 bloki
        for i in range(3):
            parent_hash = self.blockchain.get_last_block().get_hash()
            block = (
                BlockBuilder()
                .set_parent_hash(parent_hash)
                .set_author(f"miner_{i}")
                .add_document(Transaction(f"User{i}", f"User{i+1}", 100.0))
                .build(self.crypto_service, self.priv_key)
            )
            self.blockchain.append_block(block)

        # When - pobierz bloki
        blocks = self.blockchain.get_blocks_range(1, 3)

        # Then - sprawdź że dostaliśmy bloki
        assert isinstance(blocks, list)
        for block in blocks:
            assert hasattr(block, "get_hash")
            assert hasattr(block, "miner")

    def test_blockchain_validates_block_order(self):
        """Test walidacji kolejności bloków."""
        # Given - poprawny łańcuch
        for i in range(3):
            parent_hash = self.blockchain.get_last_block().get_hash()
            block = (
                BlockBuilder()
                .set_parent_hash(parent_hash)
                .set_author(f"miner_{i}")
                .add_document(Transaction(f"User{i}", f"User{i+1}", 100.0))
                .build(self.crypto_service, self.priv_key)
            )
            self.blockchain.append_block(block)

        # When
        is_valid = self.blockchain.validate_chain()

        # Then
        assert is_valid is True

    def test_empty_blockchain_operations(self):
        """Test operacji na pustym blockchainie (tylko genesis)."""
        # Given - tylko genesis
        empty_blockchain = Blockchain()

        # When/Then
        assert empty_blockchain.get_height() == 1
        assert empty_blockchain.get_last_block() is not None
        assert empty_blockchain.validate_chain() is True
