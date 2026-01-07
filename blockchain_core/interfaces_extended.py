"""
Rozszerzone interfejsy dla modułów systemu blockchain notarialnego.
Te interfejsy definiują kontrakt dla zespołów implementujących poszczególne moduły.

Zgodne z dokumentacją Design Patterns Premium.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

# ============================================================================
# MODUŁ: BUSINESS LOGIC (Sekcja 3 dokumentacji)
# ============================================================================


class DocumentType(Enum):
    """Typy dokumentów notarialnych"""

    TRANSACTION = "transaction"
    VOTING_RESULT = "voting_result"
    CONTRACT = "contract"
    SHARES_TRANSFER = "shares_transfer"
    PROPERTY_DEED = "property_deed"


class IDocumentFactory(ABC):
    """
    Abstrakcyjna fabryka dokumentów (wzorzec Factory Method).
    Zespół Business Logic powinien zaimplementować konkretne fabryki.
    """

    @abstractmethod
    def create_document(self, document_data: Dict[str, Any]):
        """
        Tworzy dokument notarialny odpowiedniego typu.

        Args:
            document_data: Dane dokumentu

        Returns:
            Instancja NotarialDocument
        """
        pass

    @abstractmethod
    def validate_document_data(self, document_data: Dict[str, Any]) -> bool:
        """
        Waliduje dane przed utworzeniem dokumentu.

        Args:
            document_data: Dane do walidacji

        Returns:
            True jeśli dane są poprawne
        """
        pass


class IBusinessLogicModule(ABC):
    """
    Interfejs głównego modułu Business Logic.
    Odpowiada za walidację biznesową i logikę smart contracts.
    """

    @abstractmethod
    def validate_transaction(self, transaction_data: Dict[str, Any], blockchain_state: Any) -> bool:
        """
        Waliduje transakcję z uwzględnieniem stanu blockchain.
        Sprawdza: saldo konta, posiadane akcje, double spending.

        Args:
            transaction_data: Dane transakcji
            blockchain_state: Aktualny stan blockchain (World State)

        Returns:
            True jeśli transakcja jest poprawna
        """
        pass

    @abstractmethod
    def execute_smart_contract(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wykonuje smart contract i zwraca rezultat.

        Args:
            contract_data: Dane kontraktu do wykonania

        Returns:
            Rezultat wykonania kontraktu
        """
        pass

    @abstractmethod
    def check_double_spending(self, document_id: str) -> bool:
        """
        Sprawdza czy dokument już istnieje w blockchain (zapobieganie double-spending).

        Args:
            document_id: Identyfikator dokumentu

        Returns:
            True jeśli dokument już istnieje
        """
        pass

    @abstractmethod
    def validate_shares_transfer(
        self, sender: str, recipient: str, shares: int, company_id: str
    ) -> bool:
        """
        Waliduje transfer udziałów w spółce.

        Args:
            sender: ID właściciela udziałów
            recipient: ID nabywcy
            shares: Liczba udziałów
            company_id: ID spółki

        Returns:
            True jeśli transfer jest możliwy
        """
        pass


# ============================================================================
# MODUŁ: NETWORK & DISCOVERY (Sekcja 4 dokumentacji)
# ============================================================================


class MessageType(Enum):
    """Typy wiadomości w protokole sieciowym"""

    HANDSHAKE = "handshake"
    TRANSACTION = "transaction"
    BLOCK = "block"
    GET_BLOCKS = "get_blocks"
    BLOCKS_RESPONSE = "blocks_response"
    PING = "ping"
    PONG = "pong"


class PeerState(Enum):
    """Stany połączenia peer"""

    CONNECTING = "connecting"
    HANDSHAKE = "handshake"
    READY = "ready"
    DISCONNECTED = "disconnected"


class INetworkModule(ABC):
    """
    Główny interfejs modułu sieciowego (NetworkManager).
    Odpowiada za komunikację P2P w sieci lokalnej.
    """

    @abstractmethod
    def start(self, port: int = 8545) -> None:
        """
        Uruchamia moduł sieciowy (discovery + TCP listener).

        Args:
            port: Port TCP do nasłuchiwania
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """Zatrzymuje moduł sieciowy."""
        pass

    @abstractmethod
    def broadcast_block(self, block: Any) -> None:
        """
        Rozgłasza nowy blok do wszystkich połączonych peerów.

        Args:
            block: Blok do rozgłoszenia
        """
        pass

    @abstractmethod
    def broadcast_transaction(self, transaction: Any) -> None:
        """
        Rozgłasza transakcję do wszystkich peerów.

        Args:
            transaction: Transakcja do rozgłoszenia
        """
        pass

    @abstractmethod
    def synchronize_chain(self) -> bool:
        """
        Synchronizuje blockchain z peerami posiadającymi dłuższy łańcuch.

        Returns:
            True jeśli synchronizacja się powiodła
        """
        pass

    @abstractmethod
    def get_peer_count(self) -> int:
        """
        Zwraca liczbę połączonych peerów.

        Returns:
            Liczba aktywnych połączeń
        """
        pass


class IConnectionListener(ABC):
    """
    Interfejs nasłuchiwania zdarzeń połączeń (wzorzec Observer).
    """

    @abstractmethod
    def on_peer_connected(self, peer_id: str, peer_info: Dict[str, Any]) -> None:
        """
        Wywoływane gdy nowy peer się połączy.

        Args:
            peer_id: Identyfikator peera
            peer_info: Informacje o peerze (adres, port, wersja)
        """
        pass

    @abstractmethod
    def on_peer_disconnected(self, peer_id: str) -> None:
        """
        Wywoływane gdy peer się rozłączy.

        Args:
            peer_id: Identyfikator peera
        """
        pass

    @abstractmethod
    def on_block_received(self, block: Any, peer_id: str) -> None:
        """
        Wywoływane gdy otrzymano blok z sieci.

        Args:
            block: Otrzymany blok
            peer_id: ID peera który wysłał blok
        """
        pass

    @abstractmethod
    def on_transaction_received(self, transaction: Any, peer_id: str) -> None:
        """
        Wywoływane gdy otrzymano transakcję.

        Args:
            transaction: Otrzymana transakcja
            peer_id: ID peera
        """
        pass


class IBlockchainInterface(ABC):
    """
    Interfejs dla modułu Network do komunikacji z Blockchain Core.
    Implementowany przez Blockchain.
    """

    @abstractmethod
    def get_height(self) -> int:
        """Zwraca wysokość łańcucha."""
        pass

    @abstractmethod
    def get_last_block(self):
        """Zwraca ostatni blok."""
        pass

    @abstractmethod
    def get_blocks_range(self, start: int, end: int) -> List[Any]:
        """Zwraca zakres bloków."""
        pass

    @abstractmethod
    def validate_and_add_block(self, block: Any) -> bool:
        """Waliduje i dodaje blok z sieci."""
        pass


# ============================================================================
# MODUŁ: IDENTITY & SECURITY (Sekcja 5 dokumentacji)
# ============================================================================


class IIdentityManager(ABC):
    """
    Zarządzanie tożsamością węzła (PKI, certyfikaty X.509).
    Zespół Security powinien zintegrować z systemem certyfikatów Izby Notarialnej.
    """

    @abstractmethod
    def load_certificate(self, cert_path: str, key_path: str, password: str) -> bool:
        """
        Wczytuje certyfikat i klucz prywatny węzła.

        Args:
            cert_path: Ścieżka do certyfikatu X.509
            key_path: Ścieżka do klucza prywatnego
            password: Hasło do klucza

        Returns:
            True jeśli wczytanie się powiodło
        """
        pass

    @abstractmethod
    def get_node_id(self) -> str:
        """
        Zwraca unikalny identyfikator węzła (z certyfikatu).

        Returns:
            ID węzła (np. Common Name z certyfikatu)
        """
        pass

    @abstractmethod
    def get_private_key(self) -> Any:
        """
        Zwraca klucz prywatny węzła.

        Returns:
            Klucz prywatny (obiekt kryptograficzny)
        """
        pass

    @abstractmethod
    def get_certificate(self) -> Any:
        """
        Zwraca certyfikat węzła.

        Returns:
            Certyfikat X.509
        """
        pass

    @abstractmethod
    def sign_data(self, data: bytes) -> bytes:
        """
        Podpisuje dane kluczem prywatnym węzła.

        Args:
            data: Dane do podpisania

        Returns:
            Podpis cyfrowy
        """
        pass


class ICertificateValidator(ABC):
    """
    Walidacja certyfikatów innych węzłów (TrustStore).
    """

    @abstractmethod
    def validate_certificate(self, certificate: Any) -> bool:
        """
        Sprawdza ważność certyfikatu (data ważności, podpis CA).

        Args:
            certificate: Certyfikat do walidacji

        Returns:
            True jeśli certyfikat jest ważny
        """
        pass

    @abstractmethod
    def is_trusted(self, certificate: Any) -> bool:
        """
        Sprawdza czy certyfikat jest podpisany przez zaufane CA.

        Args:
            certificate: Certyfikat do sprawdzenia

        Returns:
            True jeśli certyfikat jest zaufany
        """
        pass

    @abstractmethod
    def check_revocation(self, certificate: Any) -> bool:
        """
        Sprawdza czy certyfikat nie został unieważniony (CRL/OCSP).

        Args:
            certificate: Certyfikat do sprawdzenia

        Returns:
            True jeśli certyfikat NIE jest unieważniony
        """
        pass

    @abstractmethod
    def load_trusted_certificates(self, trust_store_path: str) -> bool:
        """
        Wczytuje zaufane certyfikaty CA z trust store.

        Args:
            trust_store_path: Ścieżka do trust store

        Returns:
            True jeśli wczytanie się powiodło
        """
        pass


class IKeyStore(ABC):
    """
    Bezpieczne przechowywanie kluczy prywatnych.
    """

    @abstractmethod
    def store_key(self, key_id: str, key_data: bytes, password: str) -> bool:
        """
        Zapisuje klucz z szyfrowaniem.

        Args:
            key_id: Identyfikator klucza
            key_data: Dane klucza
            password: Hasło do szyfrowania

        Returns:
            True jeśli zapis się powiódł
        """
        pass

    @abstractmethod
    def load_key(self, key_id: str, password: str) -> Optional[bytes]:
        """
        Wczytuje i deszyfruje klucz.

        Args:
            key_id: Identyfikator klucza
            password: Hasło do odszyfrowania

        Returns:
            Dane klucza lub None jeśli błąd
        """
        pass

    @abstractmethod
    def delete_key(self, key_id: str) -> bool:
        """
        Usuwa klucz z keystore.

        Args:
            key_id: Identyfikator klucza

        Returns:
            True jeśli usunięcie się powiodło
        """
        pass


# ============================================================================
# MODUŁ: STORAGE & LEDGER (Sekcja 6 dokumentacji)
# ============================================================================


class IWorldStateManager(ABC):
    """
    Zarządzanie World State (aktualny stan posiadania).
    Zespół Storage powinien zintegrować z LevelDB.
    """

    @abstractmethod
    def get_balance(self, account_id: str) -> float:
        """
        Zwraca saldo konta.

        Args:
            account_id: Identyfikator konta

        Returns:
            Saldo konta
        """
        pass

    @abstractmethod
    def get_shares(self, account_id: str, company_id: str) -> int:
        """
        Zwraca liczbę udziałów w spółce.

        Args:
            account_id: ID właściciela
            company_id: ID spółki

        Returns:
            Liczba udziałów
        """
        pass

    @abstractmethod
    def update_state(self, block: Any) -> bool:
        """
        Aktualizuje World State na podstawie transakcji w bloku.

        Args:
            block: Blok z transakcjami

        Returns:
            True jeśli aktualizacja się powiodła
        """
        pass

    @abstractmethod
    def rollback_to_height(self, height: int) -> bool:
        """
        Cofa stan do określonej wysokości łańcucha.
        Potrzebne w przypadku forka.

        Args:
            height: Wysokość do której cofnąć

        Returns:
            True jeśli rollback się powiódł
        """
        pass

    @abstractmethod
    def get_state_root(self) -> str:
        """
        Zwraca hash aktualnego stanu (Merkle root).

        Returns:
            Hash stanu
        """
        pass


class ILedgerRepository(ABC):
    """
    Repozytorium pełnej historii bloków (Ledger).
    """

    @abstractmethod
    def append_block(self, block: Any) -> bool:
        """
        Dodaje blok do ledgera (zapisuje na dysk).

        Args:
            block: Blok do zapisania

        Returns:
            True jeśli zapis się powiódł
        """
        pass

    @abstractmethod
    def get_block_by_height(self, height: int) -> Optional[Any]:
        """
        Pobiera blok po jego wysokości.

        Args:
            height: Wysokość bloku

        Returns:
            Blok lub None jeśli nie znaleziono
        """
        pass

    @abstractmethod
    def get_block_by_hash(self, block_hash: str) -> Optional[Any]:
        """
        Pobiera blok po jego hashu.

        Args:
            block_hash: Hash bloku

        Returns:
            Blok lub None
        """
        pass

    @abstractmethod
    def get_full_chain(self) -> List[Any]:
        """
        Zwraca wszystkie bloki od genesis.

        Returns:
            Lista wszystkich bloków
        """
        pass


# ============================================================================
# SYSTEM ZDARZEŃ (Sekcja 7 dokumentacji)
# ============================================================================


class EventType(Enum):
    """Typy zdarzeń w systemie"""

    BLOCK_MINED = "block_mined"
    BLOCK_RECEIVED = "block_received"
    TRANSACTION_RECEIVED = "transaction_received"
    PEER_CONNECTED = "peer_connected"
    PEER_DISCONNECTED = "peer_disconnected"
    CHAIN_SYNCHRONIZED = "chain_synchronized"
    STATE_UPDATED = "state_updated"


class IEventBus(ABC):
    """
    System zdarzeń dla komunikacji asynchronicznej między modułami.
    Wzorzec Publish-Subscribe (Sekcja 7 dokumentacji).
    """

    @abstractmethod
    def publish(self, event_type: EventType, payload: Dict[str, Any]) -> None:
        """
        Publikuje zdarzenie.

        Args:
            event_type: Typ zdarzenia
            payload: Dane zdarzenia
        """
        pass

    @abstractmethod
    def subscribe(self, event_type: EventType, handler: Callable[[Dict[str, Any]], None]) -> str:
        """
        Subskrybuje zdarzenie.

        Args:
            event_type: Typ zdarzenia
            handler: Funkcja obsługująca zdarzenie

        Returns:
            ID subskrypcji (do późniejszego unsubscribe)
        """
        pass

    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Usuwa subskrypcję.

        Args:
            subscription_id: ID subskrypcji

        Returns:
            True jeśli usunięcie się powiodło
        """
        pass


# ============================================================================
# Klasy zdarzeń (zgodnie z Tabelą 1 w dokumentacji)
# ============================================================================


class BlockMinedEvent:
    """Zdarzenie: nowy blok został wykopany"""

    def __init__(self, block: Any):
        self.event_type = EventType.BLOCK_MINED
        self.block = block
        self.hash = block.get_hash()
        self.timestamp = block.timestamp


class BlockReceivedEvent:
    """Zdarzenie: otrzymano blok z sieci"""

    def __init__(self, block: Any, peer_id: str):
        self.event_type = EventType.BLOCK_RECEIVED
        self.block = block
        self.peer_id = peer_id


class TransactionReceivedEvent:
    """Zdarzenie: otrzymano transakcję"""

    def __init__(self, transaction: Any):
        self.event_type = EventType.TRANSACTION_RECEIVED
        self.transaction = transaction
