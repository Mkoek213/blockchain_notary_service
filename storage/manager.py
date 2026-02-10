from typing import Optional, Dict
from blockchain_core.block_builder import Block
from blockchain_core.notarial_document import Transaction
from .repositories import BlockRepository, WorldStateRepository
from .json_block_repository import JsonFileBlockRepository
from .json_world_state_repository import JsonWorldStateRepository

class StorageManager:
    """
    Fasada (Facade) zarządzająca persistencją danych w systemie.
    Koordynuje zapis historii (BlockRepo) i aktualizację stanu (StateRepo).
    """

    def __init__(self, 
                 block_repo: Optional[BlockRepository] = None, 
                 state_repo: Optional[WorldStateRepository] = None):
        # Dependency Injection (lub domyślne implementacje)
        self.block_repo = block_repo or JsonFileBlockRepository()
        self.state_repo = state_repo or JsonWorldStateRepository()

    def persist_block(self, block: Block) -> bool:
        """
        Główna metoda: Zapisuje blok i aktualizuje stan świata.
        Zapewnia atomowość (w uproszczonym zakresie).
        """
        try:
            # 1. Najpierw zapisz blok w historii
            self.block_repo.save(block)
            
            # 2. Następnie zaktualizuj stan dla każdej transakcji w bloku
            processed_txs = []
            try:
                for doc in block.documents:
                    # Sprawdzamy czy dokument to Transakcja (nie np. VotingResult)
                    if isinstance(doc, Transaction):
                        self.state_repo.update_state(doc)
                        processed_txs.append(doc)
                
                # 3. Jeśli wszystko OK, zrzuć stan na dysk
                self.state_repo.save_state_to_disk()
                return True

            except Exception as e:
                print(f"Error updating state: {e}. Rolling back transactions...")
                # Rollback w pamięci dla WorldState
                for tx in reversed(processed_txs):
                    self.state_repo.rollback(tx)
                raise e # Przekaż błąd wyżej (blok został zapisany, ale stan nie - niespójność!)
                # W idealnym świecie tutaj powinniśmy też usunąć blok z pliku, 
                # ale w append-only file to trudne.
                
        except Exception as e:
            print(f"Critical storage error: {e}")
            return False

    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        return self.block_repo.find_by_hash(block_hash)

    def get_last_block(self) -> Optional[Block]:
        return self.block_repo.get_last_block()

    def get_balance(self, address: str) -> float:
        return self.state_repo.get_balance(address)
