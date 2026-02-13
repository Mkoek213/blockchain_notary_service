# Wzorce Projektowe w Module Security

## Fasada (Facade)

**Plik:** `security/identity_manager.py`

### Dlaczego ten wzorzec został użyty?
Moduł bezpieczeństwa składa się z wielu skomplikowanych i niskopoziomowych komponentów: zarządzania kluczami (`KeyStore`), weryfikacji certyfikatów (`CertificateValidator`, `TrustStore`) oraz operacji kryptograficznych. Wzorzec Fasada został użyty, aby ukryć tę złożoność przed resztą systemu (np. `NotaryService` czy `NetworkManager`). Zamiast ręcznie koordynować te obiekty, klient korzysta z jednego, prostego interfejsu `IdentityManager`.

### Zalety
- **Uproszczenie interfejsu:** Klient nie musi wiedzieć jak załadować klucz PEM czy zweryfikować łańcuch certyfikatów - wywołuje proste metody jak `load_identity()` czy `sign_data()`.
- **Luźne powiązania (Decoupling):** Zmiany w implementacji `KeyStore` lub bibliotece kryptograficznej nie wpływają na kod klienta, dopóki interfejs Fasady pozostaje ten sam.
- **Centralizacja:** Logika inicjalizacji i koordynacji komponentów bezpieczeństwa znajduje się w jednym miejscu.

### Wady
- **Ograniczenie funkcjonalności:** Fasada może nie udostępniać wszystkich zaawansowanych funkcji komponentów podrzędnych (choć w tym przypadku jest to pożądane).
- **Ryzyko "God Object":** Jeśli Fasada zacznie robić zbyt wiele, może stać się trudna w utrzymaniu.

### Przykład kodu

```python
class IdentityManager:
    """
    Fasada (Facade) dla modułu bezpieczeństwa.
    Ukrywa złożoność zarządzania kluczami, certyfikatami i walidacją.
    """
    
    def __init__(self):
        self.key_store = KeyStore()
        self.trust_store = TrustStore()
        self.validator = CertificateValidator(self.trust_store)

    def load_identity(self, key_path: str, cert_path: str, trusted_root_path: str, password: str = None):
        """Uproszczony interfejs do ładowania całej tożsamości."""
        self.key_store.load_from_files(key_path, cert_path, password)
        if os.path.exists(trusted_root_path):
            self.trust_store.load_trusted_root(trusted_root_path)

    def sign_data(self, data: bytes) -> bytes:
        """Klient nie musi wiedzieć o KeyStore ani algorytmach."""
        return self.key_store.sign(data)

    def validate_peer(self, cert: X509Certificate) -> bool:
        """Klient nie musi ręcznie wywoływać walidatora."""
        return self.validator.validate_certificate(cert)
```

---

## Adapter

**Plik:** `security/adapter.py`

### Dlaczego ten wzorzec został użyty?
W jądrze systemu (`blockchain_core`) istnieje interfejs `ICryptoService`, który został zaprojektowany wcześniej i oczekuje specyficznych sygnatur metod (np. przyjmuje klucz prywatny jako argument metody `sign_block`). Nowy moduł `security` (z `IdentityManager`) działa inaczej - zarządza kluczem wewnętrznie i nie pozwala na jego eksport. Adapter `SecurityModuleAdapter` pozwala na użycie nowej, bezpieczniejszej implementacji w starym kodzie (`Block`, `Blockchain`) bez konieczności jego przepisywania.

### Zalety
- **Kompatybilność:** Pozwala na współpracę klas o niekompatybilnych interfejsach (`ICryptoService` vs `IdentityManager`).
- **Zasada Open/Closed:** Możemy wprowadzić nowy moduł bezpieczeństwa bez modyfikowania istniejącego, przetestowanego kodu `blockchain_core`.
- **Stopniowa migracja:** Ułatwia refaktoryzację systemu, pozwalając starym komponentom działać z nową logiką.

### Wady
- **Zwiększenie złożoności:** Wprowadza dodatkową warstwę pośrednią.
- **Narzut wydajnościowy:** Drobny narzut związany z przekierowywaniem wywołań i transformacją danych.

### Przykład kodu

```python
class SecurityModuleAdapter(ICryptoService):
    """
    Adapter pozwalający używać nowego modułu security (IdentityManager)
    poprzez stary interfejs ICryptoService.
    """
    
    def __init__(self, identity_manager: IdentityManager):
        self.identity_manager = identity_manager

    # Metoda z interfejsu ICryptoService oczekuje klucza prywatnego
    def sign_block(self, block_data: Dict[str, Any], private_key: str) -> str:
        """
        Podpisuje blok używając IdentityManager.
        Parametr private_key jest ignorowany, bo IdentityManager zarządza kluczem bezpiecznie.
        """
        import json
        data_bytes = json.dumps(block_data, sort_keys=True).encode('utf-8')
        
        # Delegacja do nowego modułu
        signature = self.identity_manager.sign_data(data_bytes)
        return signature.hex()
```

---

# Wzorce Projektowe w Module Storage

## Repozytorium (Repository)

**Plik:** `blockchain_core/interfaces.py` (Interfejs), `notary_service/storage/json_storage_provider.py` (Implementacja)

### Dlaczego ten wzorzec został użyty?
System musi przechowywać bloki i stan świata w sposób trwały. Chcieliśmy odseparować logikę biznesową (np. dodawanie bloku do łańcucha) od fizycznego sposobu zapisu danych (np. plik JSON, baza SQL, baza LevelDB). Wzorzec Repozytorium definiuje abstrakcyjny interfejs (`IStorageProvider` i `BlockRepository`), a warstwa `storage` dostarcza konkretną implementację opartą na plikach JSON.

### Zalety
- **Separacja odpowiedzialności:** Logika biznesowa nie zajmuje się otwieraniem plików, parsowaniem JSON-a ani SQL-em.
- **Łatwa wymiana implementacji:** Możemy podmienić `JsonStorageProvider` na `SqlStorageProvider` bez zmieniania ani jednej linii w kodzie `Blockchain` czy `NotaryService`.
- **Testowalność:** Łatwo stworzyć `MockStorageProvider` do testów jednostkowych, który działa w pamięci i nie brudzi dysku.

### Wady
- **Wzrost liczby klas:** Dla każdego obiektu domenowego (Block, Transaction) tworzymy odpowiadające mu repozytorium.

### Przykład kodu

**Interfejs (Kontrakt):**
```python
class IStorageProvider(ABC):
    @abstractmethod
    def save_block(self, block_data: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def load_blockchain(self) -> Optional[List[Dict[str, Any]]]:
        pass
```

**Implementacja (JSON):**
```python
class JsonStorageProvider(IStorageProvider):
    def __init__(self, ledger_file: str):
        self.ledger_file = ledger_file
        self._ensure_file_exists()

    def save_block(self, block_data: Dict[str, Any]) -> bool:
        chain = self._load_data()
        chain.append(block_data)
        self._save_data(chain)
        return True
```

---

# Wzorce Projektowe w Module Blockchain Core

## Budowniczy (Builder)

**Plik:** `blockchain_core/block_builder.py`

### Dlaczego ten wzorzec został użyty?
Obiekt `Block` w systemie Proof of Authority jest skomplikowany. Posiada wiele pól konfiguracyjnych (`parentHash`, `timestamp`, `miner`, `documents`), które muszą być ustawione w odpowiedniej kolejności i zweryfikowane przed utworzeniem obiektu. Ponadto, obiekt `Block` jest niemodyfikowalny (immutable) - raz stworzony nie powinien być zmieniany (hash musi pozostać stały). Użycie konstruktora z 10 parametrami byłoby nieczytelne i podatne na błędy (tzw. "telescoping constructor"). Wzorzec Builder pozwala na czytelne, krokowe konstruowanie obiektu.

### Zalety
- **Czytelny kod klienta:** Zamiast `new Block(hash, prev, time, miner, ...)` mamy `builder.set_parent_hash(...).set_author(...)`.
- **Niemodyfikowalność produktu:** Klasa `Block` nie posiada setterów. Jest inicjalizowana tylko raz przez Buildera, co gwarantuje spójność hasha.
- **Weryfikacja spójności:** Metoda `build()` sprawdza, czy wszystkie wymagane pola zostały ustawione i automatycznie wylicza skróty kryptograficzne (`transactions_root`), zwalniając z tego klienta.

### Wady
- **Konieczność tworzenia dodatkowej klasy:** Wymaga napisania osobnej klasy `BlockBuilder`, która duplikuje część pól klasy `Block`.

### Przykład kodu

```python
class BlockBuilder:
    """
    Builder dla klasy Block.
    Umożliwia stopniowe budowanie bloku z walidacją parametrów.
    """

    def __init__(self):
        self._parent_hash = None
        self._documents = []
        # ... inne pola domyślne ...

    def set_parent_hash(self, hash: str) -> "BlockBuilder":
        self._parent_hash = hash
        return self  # Method chaining

    def add_document(self, doc: NotarialDocument) -> "BlockBuilder":
        self._documents.append(doc)
        return self

    def build(self, crypto_service=None, private_key=None) -> Block:
        # 1. Walidacja
        if self._parent_hash is None:
            raise ValueError("Parent hash required")
        
        # 2. Obliczenia automatyczne (np. Merkle Root)
        self._calculate_roots()

        # 3. Utworzenie obiektu
        block = Block(self)

        # 4. Opcjonalne podpisanie
        if crypto_service:
            block.sign_block(private_key, crypto_service)
            
        return block
```

---

# Wzorce Projektowe w Module Business Logic

## Metoda Wytwórcza (Factory Method)

**Plik:** `business_logic/document_providers.py`

### Dlaczego ten wzorzec został użyty?
System obsługuje różne typy dokumentów notarialnych (np. `SharesTransfer`, `Dividend`, `Resolution`), które różnią się strukturą danych i regułami walidacji. Zamiast tworzyć jeden wielki blok warunkowy (`if/else` lub `switch`) decydujący o tym, jaką klasę utworzyć, zastosowano wzorzec Metody Wytwórczej. Abstrakcyjna klasa `DocumentProvider` definiuje interfejs tworzenia, a konkretne podklasy (`FinancialActionProvider`, `GovernanceActionProvider`) implementują logikę dla specyficznych grup dokumentów.

### Zalety
- **Zasada Open/Closed:** Dodanie nowego typu dokumentu (np. `RealEstateTransfer`) wymaga jedynie dodania nowego providera, bez modyfikacji istniejącego kodu.
- **Zasada Pojedynczej Odpowiedzialności (SRP):** Logika walidacji i tworzenia obiektów jest odseparowana od reszty systemu i zgrupowana tematycznie.
- **Enkapsulacja:** Klient systemu nie musi znać szczegółów konstrukcji poszczególnych klas dokumentów.

### Wady
- **Zwiększona liczba klas:** Dla każdej rodziny dokumentów potrzebna jest osobna klasa providera.

### Przykład kodu

```python
class DocumentProvider(ABC):
    """
    Abstrakcyjny Twórca (Creator).
    Definiuje metodę wytwórczą _create oraz publiczne API create_document.
    """
    
    def create_document(self, document_data: Dict[str, Any]) -> NotarialDocument:
        # Wspólna logika (np. wstępna walidacja)
        if not self.validate_document_data(document_data):
            raise ValueError("Invalid data")
            
        # Wywołanie metody wytwórczej
        return self._create(document_data)

    @abstractmethod
    def _create(self, document_data: Dict[str, Any]) -> NotarialDocument:
        """Metoda wytwórcza implementowana przez podklasy."""
        pass

class FinancialActionProvider(DocumentProvider):
    """
    Konkretny Twórca (Concrete Creator) dla operacji finansowych.
    """
    
    def _create(self, document_data: Dict[str, Any]) -> NotarialDocument:
        doc_type = document_data["type"]
        
        if doc_type == "SharesTransfer":
            return SharesTransfer(...) # Tworzenie konkretnego produktu
        elif doc_type == "Dividend":
            return Dividend(...)
            
        raise ValueError(f"Unknown type: {doc_type}")
```
