"""
PRZYKŁADY INTEGRACJI Z BLOCKCHAIN CORE
========================================

Ten plik pokazuje JAK pozostałe zespoły (Business Logic, Network, Security, Storage)
powinny używać interfejsów dostarczonych przez moduł Blockchain Core.

BLOCKCHAIN CORE (już zaimplementowany) dostarcza:
    ✓ Block, BlockBuilder - tworzenie i zarządzanie blokami
    ✓ Blockchain - zarządzanie łańcuchem bloków
    ✓ NotarialDocument (Transaction, VotingResult) - typy dokumentów
    ✓ EventBus - komunikacja między modułami
    ✓ Interfejsy: IDocumentFactory, INetworkModule, IBusinessLogicModule,
                  IBlockchainInterface, IWorldStateManager, etc.

ZESPOŁY IMPLEMENTUJĄ (przykłady poniżej):
    □ Moduł 2: Business Logic - walidacja dokumentów, smart contracts
    □ Moduł 3: Network - P2P komunikacja, synchronizacja
    □ Moduł 4: Security - PKI, zarządzanie tożsamością
    □ Moduł 5: Storage - World State, persystencja

UWAGA: To są PRZYKŁADY implementacji pokazujące jak używać Blockchain Core!
"""

from typing import Any, Dict

# Interfejsy do implementacji przez zespoły; Gotowe komponenty z Blockchain Core
from blockchain_core import (
    BlockBuilder,
    Blockchain,
    EventBus,
    EventType,
    IBlockchainInterface,
    IBusinessLogicModule,
    IDocumentFactory,
    INetworkModule,
    NotarialDocument,
    Transaction,
    VotingResult,
)
from blockchain_core.mock_crypto import MockCryptoService

# ============================================================================
# MODUŁ 2: BUSINESS LOGIC - Wzorzec Factory dla dokumentów
# ============================================================================
# Zespół Business Logic implementuje fabrykę dokumentów notarialnych
# zgodnie z interfejsem IDocumentFactory z Blockchain Core


class NotarialDocumentFactory(IDocumentFactory):
    """
    Fabryka dokumentów notarialnych (wzorzec Factory Method).
    Tworzy odpowiedni typ dokumentu na podstawie danych wejściowych.
    """

    def create_document(self, document_data: Dict[str, Any]) -> NotarialDocument:
        """Tworzy dokument notarialny odpowiedniego typu z walidacją."""
        if not self.validate_document_data(document_data):
            raise ValueError("Invalid document data")

        document_type = document_data.get("type")

        if document_type == "Transaction":
            return self._create_transaction(document_data)
        elif document_type == "VotingResult":
            return self._create_voting_result(document_data)
        else:
            raise ValueError(f"Unknown document type: {document_type}")

    def validate_document_data(self, document_data: Dict[str, Any]) -> bool:
        """Waliduje podstawowe dane dokumentu."""
        if "type" not in document_data:
            return False

        document_type = document_data["type"]

        if document_type == "Transaction":
            return self._validate_transaction(document_data)
        elif document_type == "VotingResult":
            return self._validate_voting_result(document_data)

        return False

    def _create_transaction(self, document_data: Dict[str, Any]) -> Transaction:
        """Tworzy dokument Transaction."""
        transaction = Transaction(
            sender=document_data["sender"],
            recipient=document_data["recipient"],
            amount=document_data["amount"],
        )

        if "signatures" in document_data:
            for sig in document_data["signatures"]:
                transaction.add_signature(sig)

        return transaction

    def _validate_transaction(self, document_data: Dict[str, Any]) -> bool:
        """Waliduje dane dla Transaction."""
        required_fields = ["sender", "recipient", "amount"]

        if not all(field in document_data for field in required_fields):
            return False

        if document_data["amount"] <= 0:
            return False

        return True

    def _create_voting_result(self, document_data: Dict[str, Any]) -> VotingResult:
        """Tworzy dokument VotingResult."""
        voting = VotingResult(
            voting_id=document_data["voting_id"], results=document_data["results"]
        )

        if "signatures" in document_data:
            for sig in document_data["signatures"]:
                voting.add_signature(sig)

        return voting

    def _validate_voting_result(self, document_data: Dict[str, Any]) -> bool:
        """Waliduje dane dla VotingResult."""
        required = ["voting_id", "results"]
        if not all(field in document_data for field in required):
            return False

        if not isinstance(document_data["results"], dict):
            return False

        return True


class DocumentFactoryRegistry:
    """
    Rejestr fabryki dokumentów (wzorzec Factory Method).
    Zespół Business Logic używa jednej fabryki do tworzenia wszystkich typów dokumentów.
    """

    def __init__(self):
        self.factory = NotarialDocumentFactory()

    def create_document(self, document_data: Dict[str, Any]) -> Any:
        """Tworzy dokument używając fabryki."""
        return self.factory.create_document(document_data)


# ============================================================================
# ZESPÓŁ BUSINESS LOGIC - Walidacja biznesowa
# ============================================================================


class SharesValidator(IBusinessLogicModule):
    """
    Walidacja operacji na udziałach.
    Zespół Business Logic sprawdza logikę biznesową.
    """

    def __init__(self, world_state_manager):
        """
        Args:
            world_state_manager: Dostęp do aktualnego stanu posiadania
        """
        self.world_state = world_state_manager

    def validate_transaction(self, transaction_data: Dict[str, Any], blockchain_state: Any) -> bool:
        """
        Waliduje transakcję z uwzględnieniem stanu blockchain.
        """
        # Przykład: sprawdzenie czy sprzedający ma wystarczająco udziałów
        if "seller_id" in transaction_data and "shares_count" in transaction_data:
            seller_id = transaction_data["seller_id"]
            shares_count = transaction_data["shares_count"]
            company_id = transaction_data["company_id"]

            # Pobierz obecną liczbę udziałów sprzedającego
            current_shares = self.world_state.get_shares(seller_id, company_id)

            # Sprawdź czy ma wystarczająco
            if current_shares < shares_count:
                print(
                    f"❌ Walidacja: {seller_id} ma tylko {current_shares} udziałów, "
                    f"chce sprzedać {shares_count}"
                )
                return False

        return True

    def execute_smart_contract(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """Wykonuje logikę smart contract."""
        # Zespół implementuje logikę kontraktów
        return {"status": "executed"}

    def check_double_spending(self, document_id: str) -> bool:
        """Sprawdza czy dokument już istnieje."""
        # Zespół implementuje sprawdzanie duplikatów
        return False

    def validate_shares_transfer(
        self, sender: str, recipient: str, shares: int, company_id: str
    ) -> bool:
        """Waliduje transfer udziałów."""
        # Sprawdź czy nadawca ma udziały
        sender_shares = self.world_state.get_shares(sender, company_id)
        if sender_shares < shares:
            return False

        # Sprawdź czy firma istnieje
        company = self.world_state.get_company(company_id)
        if not company:
            return False

        return True


# ============================================================================
# ZESPÓŁ NETWORK - Komunikacja P2P
# ============================================================================


class SimpleNetworkManager(INetworkModule):
    """
    Przykładowa implementacja modułu sieciowego.
    Zespół Network implementuje pełną komunikację P2P.
    """

    def __init__(self, blockchain: IBlockchainInterface, event_bus: EventBus):
        """
        Args:
            blockchain: Interfejs do blockchain core
            event_bus: System zdarzeń
        """
        self.blockchain = blockchain
        self.event_bus = event_bus
        self.peers: Dict[str, Any] = {}  # peer_id -> connection
        self.is_running = False

        # Subskrybuj zdarzenia blockchain
        self.event_bus.subscribe(EventType.BLOCK_MINED, self._on_block_mined)

    def start(self, port: int = 8545) -> None:
        """Uruchamia moduł sieciowy."""
        print(f"[Network] Uruchamiam na porcie {port}")
        # Zespół implementuje:
        # - Multicast discovery (UDP)
        # - TCP listener
        # - Handshake protocol
        self.is_running = True

    def stop(self) -> None:
        """Zatrzymuje moduł."""
        print("[Network] Zatrzymuję moduł sieciowy")
        self.is_running = False
        # Zespół zamyka połączenia

    def broadcast_block(self, block) -> None:
        """Rozgłasza blok do wszystkich peerów."""
        print(f"[Network] Rozgłaszam blok {block.get_hash()[:8]}... do {len(self.peers)} peerów")

        # Zespół implementuje:
        # for peer_id, connection in self.peers.items():
        #     connection.send_message({
        #         'type': 'NEW_BLOCK',
        #         'block': block.to_dict()
        #     })

    def broadcast_transaction(self, transaction) -> None:
        """Rozgłasza transakcję."""
        print(f"[Network] Rozgłaszam transakcję do {len(self.peers)} peerów")
        # Zespół implementuje wysyłanie

    def synchronize_chain(self) -> bool:
        """Synchronizuje blockchain z siecią."""
        print("[Network] Synchronizuję blockchain...")

        # Zespół implementuje:
        # 1. Zapytaj wszystkich peerów o wysokość łańcucha
        # my_height = self.blockchain.get_height()
        # max_height = my_height
        # best_peer = None

        # for peer_id, connection in self.peers.items():
        #     peer_height = connection.get_blockchain_height()
        #     if peer_height > max_height:
        #         max_height = peer_height
        #         best_peer = peer_id

        # 2. Jeśli znaleziono dłuższy łańcuch, pobierz bloki
        # if best_peer:
        #     blocks = self.peers[best_peer].get_blocks_range(my_height, max_height)
        #     for block in blocks:
        #         self.blockchain.validate_and_add_block(block)

        return False

    def get_peer_count(self) -> int:
        """Zwraca liczbę połączeń."""
        return len(self.peers)

    def _on_block_mined(self, payload: Dict[str, Any]):
        """Callback gdy wykopano nowy blok."""
        block = payload["block"]
        # Automatycznie rozgłoś
        self.broadcast_block(block)


# ============================================================================
# DEMO - Użycie przez zespoły
# ============================================================================


def demo_teams_integration():
    """
    Pokazuje jak zespoły używają interfejsów z blockchain_core.
    """
    print("=" * 70)
    print("DEMO: Integracja modułów zespołów")
    print("=" * 70)
    print()

    # ========================================================================
    # 1. MODUŁ BUSINESS LOGIC - Tworzenie dokumentów przez fabrykę
    # ========================================================================
    print("=" * 70)
    print("MODUŁ 2: Business Logic - Wzorzec Factory")
    print("=" * 70)
    print("Zespół implementuje: IDocumentFactory")
    print("Używa z Blockchain Core: NotarialDocument, Transaction, VotingResult")
    print("-" * 70)

    factory = NotarialDocumentFactory()

    # Przykład 1: Tworzenie Transaction
    transaction_data = {
        "type": "Transaction",
        "sender": "Alice",
        "recipient": "Bob",
        "amount": 1000.0,
    }

    transaction = factory.create_document(transaction_data)
    print(f"✓ Utworzono dokument: {type(transaction).__name__}")
    print(f"  Nadawca: {transaction.sender}")
    print(f"  Odbiorca: {transaction.recipient}")
    print(f"  Kwota: {transaction.amount}")
    print(f"  JSON: {transaction.get_json_data()[:80]}...")

    # Przykład 2: Tworzenie VotingResult
    voting_data = {
        "type": "VotingResult",
        "voting_id": "VOTE-2026-001",
        "results": {"Option A": 150, "Option B": 120, "Option C": 80},
    }

    voting = factory.create_document(voting_data)
    print(f"\n✓ Utworzono dokument: {type(voting).__name__}")
    print(f"  ID głosowania: {voting.voting_id}")
    print(f"  Wyniki: {voting.results}")
    print()

    # ========================================================================
    # 2. MODUŁ BUSINESS LOGIC - Walidacja biznesowa + Integracja z Blockchain
    # ========================================================================
    print("=" * 70)
    print("MODUŁ 2: Business Logic - Walidacja + Integracja")
    print("=" * 70)
    print("Zespół implementuje: IBusinessLogicModule")
    print("Używa z Blockchain Core: Blockchain, BlockBuilder, EventBus")
    print("-" * 70)

    # Inicjalizacja komponentów Blockchain Core
    blockchain = Blockchain()
    crypto_service = MockCryptoService()
    event_bus = EventBus()
    pub_key, priv_key = crypto_service.generate_key_pair()

    # Mock World State (zespół Storage to zaimplementuje później)
    class MockWorldState:
        def get_shares(self, shareholder_id, company_id):
            return 50 if shareholder_id == "Alice" else 0

        def get_company(self, company_id):
            return {"id": company_id, "name": "Example Company"}

    validator = SharesValidator(MockWorldState())

    # Test walidacji
    valid_transfer = {"company_id": "COMP-001", "seller_id": "Alice", "shares_count": 10}

    is_valid = validator.validate_transaction(valid_transfer, None)
    print(f"✓ Walidacja transferu (Alice, 10 udziałów): {'PASS' if is_valid else 'FAIL'}")

    # Integracja: Tworzenie bloku z walidowanymi dokumentami
    if is_valid:
        # Użycie BlockBuilder z Blockchain Core
        builder = BlockBuilder()
        block = (
            builder.set_parent_hash(blockchain.get_last_block().get_hash())
            .set_author("notary_alice")
            .add_document(transaction)
            .add_document(voting)
            .build(crypto_service, priv_key)
        )

        blockchain.append_block(block)
        print(f"✓ Blok dodany do łańcucha: {block.get_hash()[:16]}...")
        print(f"✓ Wysokość łańcucha: {blockchain.get_height()}")
    print()

    # ========================================================================
    # 3. MODUŁ NETWORK - Komunikacja P2P i Synchronizacja
    # ========================================================================
    print("=" * 70)
    print("MODUŁ 3: Network - Komunikacja P2P")
    print("=" * 70)
    print("Zespół implementuje: INetworkModule")
    print("Używa z Blockchain Core: IBlockchainInterface, EventBus, Block")
    print("-" * 70)

    network = SimpleNetworkManager(blockchain, event_bus)

    network.start(port=8545)
    print("✓ Moduł sieciowy uruchomiony na porcie 8545")
    print(f"✓ Połączonych peerów: {network.get_peer_count()}")

    # Symulacja rozgłaszania bloku przez EventBus
    print("\n✓ Rozgłaszanie nowo utworzonego bloku...")
    network.broadcast_block(block)

    # Symulacja synchronizacji
    print("✓ Synchronizacja łańcucha z siecią...")
    network.synchronize_chain()

    network.stop()
    print()

    # ========================================================================
    # PODSUMOWANIE INTEGRACJI
    # ========================================================================
    print("=" * 70)
    print("✅ PODSUMOWANIE INTEGRACJI Z BLOCKCHAIN CORE")
    print("=" * 70)
    print()
    print("BLOCKCHAIN CORE (zaimplementowany) dostarcza:")
    print("  ✓ Block, BlockBuilder - tworzenie bloków")
    print("  ✓ Blockchain - zarządzanie łańcuchem")
    print("  ✓ NotarialDocument, Transaction, VotingResult - typy dokumentów")
    print("  ✓ EventBus - komunikacja między modułami (Pub-Sub)")
    print("  ✓ Interfejsy - kontrakty dla zespołów")
    print()
    print("ZESPOŁY IMPLEMENTUJĄ (używając interfejsów):")
    print("  □ Moduł 2 (Business Logic):")
    print("      - IDocumentFactory - tworzenie dokumentów")
    print("      - IBusinessLogicModule - walidacja biznesowa")
    print("  □ Moduł 3 (Network):")
    print("      - INetworkModule - P2P komunikacja")
    print("      - IConnectionListener - zarządzanie połączeniami")
    print("  □ Moduł 4 (Security):")
    print("      - IIdentityManager - PKI/X.509")
    print("      - ICertificateValidator - walidacja certyfikatów")
    print("  □ Moduł 5 (Storage):")
    print("      - IWorldStateManager - World State pattern")
    print("      - IStorageProvider - persystencja danych")
    print()
    print("KOMUNIKACJA: EventBus umożliwia luźne sprzężenie między modułami")
    print("=" * 70)


if __name__ == "__main__":
    demo_teams_integration()
