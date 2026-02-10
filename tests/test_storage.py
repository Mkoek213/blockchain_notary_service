import os
import pytest
from blockchain_core.block_builder import BlockBuilder
from blockchain_core.notarial_document import Transaction
from storage import StorageManager, JsonFileBlockRepository, JsonWorldStateRepository

TEST_LEDGER = "test_ledger.json"
TEST_STATE = "test_world_state.json"

@pytest.fixture
def storage_manager():
    # Setup: usuń stare pliki testowe
    if os.path.exists(TEST_LEDGER): os.remove(TEST_LEDGER)
    if os.path.exists(TEST_STATE): os.remove(TEST_STATE)
    
    # Inicjalizacja z testowymi ścieżkami
    block_repo = JsonFileBlockRepository(TEST_LEDGER)
    state_repo = JsonWorldStateRepository(TEST_STATE)
    
    # Seed początkowy dla Alice (żeby nie miała ujemnego salda)
    state_repo.balances["Alice"] = 1000.0
    state_repo.save_state_to_disk()
    
    manager = StorageManager(block_repo, state_repo)
    yield manager
    
    # Teardown: sprzątanie (opcjonalne)
    if os.path.exists(TEST_LEDGER): os.remove(TEST_LEDGER)
    if os.path.exists(TEST_STATE): os.remove(TEST_STATE)

def test_persist_block_updates_state(storage_manager):
    # 1. Sprawdź stan początkowy
    assert storage_manager.get_balance("Alice") == 1000.0
    assert storage_manager.get_balance("Bob") == 0.0
    
    # 2. Stwórz blok z transakcją
    tx = Transaction("Alice", "Bob", 100.0)
    
    builder = BlockBuilder()
    builder.set_parent_hash("0" * 64)
    builder.set_author("Miner1")
    builder.add_document(tx)
    block = builder.build()
    
    # 3. Zapisz blok przez Fasada
    success = storage_manager.persist_block(block)
    assert success is True
    
    # 4. Sprawdź czy stan się zaktualizował (World State)
    assert storage_manager.get_balance("Alice") == 900.0
    assert storage_manager.get_balance("Bob") == 100.0
    
    # 5. Sprawdź czy blok zapisał się w historii (Ledger)
    last_block = storage_manager.get_last_block()
    assert last_block is not None
    assert last_block.hash == block.hash
    assert len(last_block.documents) == 1

def test_state_persistence_reload():
    # Test czy stan ładuje się poprawnie po "restarcie" (nowa instancja repo)
    if os.path.exists(TEST_STATE): os.remove(TEST_STATE)
    
    # Zapisz coś
    repo1 = JsonWorldStateRepository(TEST_STATE)
    repo1.balances["Charlie"] = 50.0
    repo1.save_state_to_disk()
    
    # Załaduj w nowej instancji
    repo2 = JsonWorldStateRepository(TEST_STATE)
    assert repo2.get_balance("Charlie") == 50.0
