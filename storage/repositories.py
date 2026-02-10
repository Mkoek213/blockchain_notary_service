from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from blockchain_core.block_builder import Block
from blockchain_core.notarial_document import Transaction

class BlockRepository(ABC):
    """
    Interfejs repozytorium do zarządzania trwałością bloków (Ledger).
    """
    
    @abstractmethod
    def save(self, block: Block) -> None:
        """Zapisuje nowy blok w historii."""
        pass

    @abstractmethod
    def find_by_hash(self, block_hash: str) -> Optional[Block]:
        """Pobiera blok na podstawie jego hasha."""
        pass

    @abstractmethod
    def get_last_block(self) -> Optional[Block]:
        """Zwraca ostatni blok w łańcuchu (head)."""
        pass
        
    @abstractmethod
    def get_all_blocks(self) -> List[Block]:
        """Zwraca całą historię łańcucha."""
        pass


class WorldStateRepository(ABC):
    """
    Interfejs repozytorium do zarządzania aktualnym stanem świata (World State).
    Przechowuje np. aktualny podział udziałów w firmach.
    """

    @abstractmethod
    def update_state(self, tx: Transaction) -> None:
        """Aplikuje zmiany z transakcji do stanu świata."""
        pass

    @abstractmethod
    def rollback(self, tx: Transaction) -> None:
        """Cofa zmiany transakcji (w przypadku forka/błędu)."""
        pass

    @abstractmethod
    def get_balance(self, address: str) -> float:
        """Zwraca aktualny stan posiadania dla danego adresu."""
        pass

    @abstractmethod
    def save_state_to_disk(self) -> None:
        """Zrzuca stan pamięci na dysk."""
        pass
