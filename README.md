# Blockchain Core - Moduł Bazowy

[![Version](https://img.shields.io/badge/version-0.4.0-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

## 📋 O Projekcie

**blockchain-core** to implementacja modułu Blockchain Core dla systemu notarialnego. Projekt realizuje podstawową funkcjonalność blockchain z wzorcem Builder i dostarcza interfejsy dla pozostałych modułów.

## 🎯 Co zostało zaimplementowane

### Blockchain Core (✅ Gotowe)

**1. Block z wzorcem Builder**
- Klasa `Block` - reprezentacja bloku zgodna z dokumentacją
- `BlockBuilder` - fluent API do konstruowania bloków
- Pola: `previousHash`, `hash`, `timestamp`, `documents`, `miner`, `transactionsRoot`, `stateRoot`, `extraData`

**2. Blockchain**
- Zarządzanie łańcuchem bloków
- Walidacja bloków i łańcucha
- Metody dla Network: `get_height()`, `get_blocks_range()`, `validate_and_add_block()`

**3. NotarialDocument**
- Interfejs bazowy dla dokumentów notarialnych
- Przykładowe implementacje: `Transaction`, `VotingResult`

**4. EventBus (Pub-Sub)**
- Komunikacja między modułami bez ścisłego sprzężenia
- 7 typów zdarzeń: `BLOCK_ADDED`, `BLOCK_VALIDATED`, `DOCUMENT_ADDED`, etc.

**5. Interfejsy dla zespołów**
- `IDocumentFactory` - Factory pattern (Business Logic)
- `IBusinessLogicModule` - walidacja dokumentów (Business Logic)
- `INetworkModule` - komunikacja P2P (Network)
- `IIdentityManager` - PKI/X.509 (Security)
- `IWorldStateManager` - World State pattern (Storage)
- `IStorageProvider`, `IConsensusProvider`, `ICryptoService` - podstawowe interfejsy

## 🚀 Jak z tego korzystać

### Instalacja

```bash
pip install -e .
```

### Tworzenie bloków (wzorzec Builder)

```python
from blockchain_core import BlockBuilder, Blockchain

# Pobierz hash ostatniego bloku
blockchain = Blockchain()
parent_hash = blockchain.get_last_block().get_hash()

# Zbuduj nowy blok
builder = BlockBuilder()
block = builder \
    .set_parent_hash(parent_hash) \
    .add_document(document) \
    .set_author("notary_id") \
    .build()

# Dodaj do łańcucha
blockchain.append_block(block)
```

### Tworzenie własnych dokumentów

```python
from blockchain_core import NotarialDocument

class MyDocument(NotarialDocument):
    def __init__(self, data):
        self.data = data

    def get_json_data(self) -> str:
        return json.dumps(self.data)

    def to_dict(self) -> dict:
        return self.data
```

### Komunikacja między modułami (EventBus)

```python
from blockchain_core import EventBus, EventType

event_bus = EventBus()

# Subskrypcja
def on_block_added(data):
    print(f"Nowy blok: {data['block'].get_hash()}")

sub_id = event_bus.subscribe(EventType.BLOCK_ADDED, on_block_added)

# Publikacja
event_bus.publish(EventType.BLOCK_ADDED, {"block": block})
```

## 👥 Dla zespołów implementujących moduły

### Business Logic - Wzorzec Factory Method (Metoda Wytwórcza)

Moduł `business_logic` wykorzystuje wzorzec **Factory Method** do tworzenia dokumentów notarialnych.
Wzorzec eliminuje centralne struktury `switch-case` — każdy typ dokumentu ma swojego wyspecjalizowanego dostawcę.

#### Struktura klas

```
DocumentProvider (abstrakcja — Creator)
├── FinancialActionProvider     → tworzy: SharesTransfer, Dividend
└── GovernanceActionProvider    → tworzy: Resolution
```

- **`DocumentProvider`** — abstrakcyjna klasa bazowa definiująca interfejs metody wytwórczej:
  - `get_supported_types()` — lista obsługiwanych typów
  - `create_document(data)` — walidacja + delegacja do `_create()`
  - `_create(data)` — metoda wytwórcza (implementowana w podklasach)
  - `validate_document_data(data)` — weryfikacja danych wejściowych

- **`FinancialActionProvider`** — obsługuje operacje kapitałowe (`SharesTransfer`, `Dividend`)
- **`GovernanceActionProvider`** — obsługuje decyzje zarządcze (`Resolution`)

#### Jak tworzyć dokumenty (przez `DocumentRegistry`)

`DocumentRegistry` jest routerem, który iteruje po zarejestrowanych providerach — **bez switch-case**:

```python
from notary_service import DocumentRegistry

registry = DocumentRegistry()  # domyślnie: Financial + Governance

# Tworzenie transferu udziałów (obsłuży FinancialActionProvider)
transfer = registry.create_document({
    "type": "SharesTransfer",
    "seller": "Jan Kowalski",
    "buyer": "Anna Nowak",
    "company_id": "COMP-001",
    "shares_count": 100,
    "price_per_share": 50.0,
})

# Tworzenie uchwały (obsłuży GovernanceActionProvider)
resolution = registry.create_document({
    "type": "Resolution",
    "resolution_id": "RES-2025-001",
    "company_id": "COMP-001",
    "resolution_type": "dividend_approval",
    "votes_for": 75,
    "votes_against": 25,
})
```

#### Jak dodać nowy typ dokumentu (Open/Closed Principle)

Aby dodać nowy typ czynności notarialnej, wystarczy stworzyć nowy provider — **bez modyfikacji istniejącego kodu**:

```python
from business_logic.document_providers import DocumentProvider

class InsuranceActionProvider(DocumentProvider):
    """Nowy provider dla dokumentów ubezpieczeniowych."""

    def get_supported_types(self) -> list:
        return ["InsurancePolicy"]

    def validate_document_data(self, document_data):
        required = ["policy_id", "insured_party", "premium"]
        return all(f in document_data for f in required)

    def _create(self, document_data):
        return InsurancePolicy(**document_data)

# Rejestracja razem z istniejącymi providerami:
registry = DocumentRegistry(providers=[
    FinancialActionProvider(),
    GovernanceActionProvider(),
    InsuranceActionProvider(),  # nowy provider
])
```

#### Przepływ tworzenia dokumentu

```
Klient (np. UI)
    │
    ▼
DocumentRegistry.create_document(data)
    │
    ├── FinancialActionProvider.get_supported_types() → ["SharesTransfer", "Dividend"]
    │       └── (jeśli pasuje) → validate → _create() → SharesTransfer / Dividend
    │
    ├── GovernanceActionProvider.get_supported_types() → ["Resolution"]
    │       └── (jeśli pasuje) → validate → _create() → Resolution
    │
    └── (żaden provider?) → GenericNotarialDocument (fallback)
```

### Business Logic - Walidacja

```python
from blockchain_core import IBusinessLogicModule

class DocumentValidator(IBusinessLogicModule):
    def validate_document(self, document: NotarialDocument) -> bool:
        # Twoja logika walidacji biznesowej
        return True
```

### Network - P2P Communication

```python
from blockchain_core import INetworkModule, IBlockchainInterface

class P2PNetwork(INetworkModule):
    def __init__(self, blockchain: IBlockchainInterface):
        self.blockchain = blockchain

    def start(self, port: int):
        # Uruchom węzeł P2P
        pass

    def broadcast_block(self, block):
        # Rozgłoś blok do sieci
        pass
```

### Security - PKI/X.509

```python
from blockchain_core import IIdentityManager

class PKIManager(IIdentityManager):
    def verify_certificate(self, cert_data: bytes) -> bool:
        # Weryfikacja certyfikatu notariusza
        pass
```

### Storage - Persistence

```python
from blockchain_core import IStorageProvider

class PostgresStorage(IStorageProvider):
    def save_block(self, block_data: dict) -> bool:
        # Zapisz blok do bazy danych
        pass

    def load_blockchain(self) -> list:
        # Wczytaj łańcuch z bazy
        pass
```

## 📂 Struktura projektu

```
blockchain_core/
├── __init__.py              # Eksporty modułu
├── block_builder.py         # Block + BlockBuilder (Builder pattern)
├── blockchain.py            # Zarządzanie łańcuchem
├── notarial_document.py     # Interfejs NotarialDocument + przykłady
├── crypto_service.py        # ICryptoService interface
├── event_bus.py             # EventBus (Pub-Sub)
├── interfaces.py            # Podstawowe interfejsy
├── interfaces_extended.py   # Wszystkie interfejsy dla zespołów
├── mock_crypto.py           # Mock crypto (do testów)
└── mock_providers.py        # Mock providers (do testów)

examples/
├── demo_builder.py              # Demo wzorca Builder
├── demo_company_operations.py   # Demo operacji na spółkach
├── teams_integration_example.py # JAK zespoły implementują moduły
└── company_documents.py         # Przykładowe typy dokumentów
```

## 🔗 Dependency Injection

Blockchain akceptuje implementacje interfejsów przez constructor injection:

```python
from blockchain_core import Blockchain

blockchain = Blockchain(
    storage_provider=YourStorage(),
    consensus_provider=YourConsensus(),
    notary_validator=YourValidator(),
    crypto_service=YourCrypto()
)
```

## 📚 Przykłady

### Demo 1: Builder Pattern
```bash
python examples/demo_builder.py
```
Pokazuje sekwencję tworzenia bloków zgodnie z diagramem z dokumentacji.

### Demo 2: Integracja zespołów
```bash
python examples/teams_integration_example.py
```
**Najważniejsze!** Pokazuje jak każdy zespół może zaimplementować swój moduł:
- Business Logic - Factory pattern, walidacja
- Network - P2P communication
- Wszystkie używają EventBus do komunikacji

## 🤝 Współpraca

1. **Sklonuj repo**
2. **Zainstaluj**: `pip install -e .`
3. **Zobacz przykłady**: `python examples/teams_integration_example.py`
4. **Implementuj swój moduł** używając interfejsów z `blockchain_core`
5. **Używaj EventBus** do komunikacji między modułami

## 📝 Licencja

MIT License

## 👤 Autor

Moduł Blockchain Core - implementacja bazowa dla systemu notarialnego
