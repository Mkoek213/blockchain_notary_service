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
