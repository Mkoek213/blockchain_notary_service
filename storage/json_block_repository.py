import os
import json
from typing import Optional, List, Dict
from .repositories import BlockRepository
from .serializer import JsonSerializer
from blockchain_core.block_builder import Block, BlockBuilder
from blockchain_core.notarial_document import Transaction, VotingResult

class JsonFileBlockRepository(BlockRepository):
    """
    Implementacja repozytorium bloków oparta na pliku JSON.
    """
    
    def __init__(self, file_path: str = "ledger.json"):
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump([], f)

    def save(self, block: Block) -> None:
        """Zapisuje blok poprzez dopisanie go do listy w pliku JSON."""
        blocks = self._load_raw_data()
        
        # Konwertujemy blok do dict używając jego natywnej metody
        block_data = block.to_dict()
        blocks.append(block_data)
        
        with open(self.file_path, "w") as f:
            # Używamy naszego serializera dla spójności formatowania
            f.write(JsonSerializer.serialize(blocks))

    def find_by_hash(self, block_hash: str) -> Optional[Block]:
        blocks_data = self._load_raw_data()
        for b_data in blocks_data:
            if b_data.get("hash") == block_hash:
                return self._reconstruct_block(b_data)
        return None

    def get_last_block(self) -> Optional[Block]:
        blocks_data = self._load_raw_data()
        if not blocks_data:
            return None
        return self._reconstruct_block(blocks_data[-1])

    def get_all_blocks(self) -> List[Block]:
        blocks_data = self._load_raw_data()
        return [self._reconstruct_block(b) for b in blocks_data]

    def _load_raw_data(self) -> List[Dict]:
        """Pobiera surowe dane JSON."""
        try:
            with open(self.file_path, "r") as f:
                content = f.read()
                if not content:
                    return []
                return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _reconstruct_block(self, data: Dict) -> Block:
        """
        Odtwarza obiekt Block z surowych danych słownikowych.
        To jest trudny moment, bo BlockBuilder oczekuje ustawiania pól,
        a Block jest immutable.
        """
        builder = BlockBuilder()
        builder.set_parent_hash(data["previous_hash"])
        builder.set_timestamp(data["timestamp"])
        builder.set_author(data["miner"])
        builder.set_roots(data["transactions_root"], data["state_root"])
        
        # Odtwarzanie dokumentów
        for doc_data in data.get("documents", []):
            if doc_data.get("type") == "Transaction":
                tx = Transaction(
                    doc_data["sender"],
                    doc_data["recipient"],
                    doc_data["amount"]
                )
                # Odtwarzanie podpisów transakcji
                for sig in doc_data.get("signatures", []):
                    tx.add_signature(sig)
                builder.add_document(tx)
                
            elif doc_data.get("type") == "VotingResult":
                vr = VotingResult(
                    doc_data["voting_id"],
                    doc_data["results"]
                )
                for sig in doc_data.get("signatures", []):
                    vr.add_signature(sig)
                builder.add_document(vr)

        # Build tworzy nowy hash, ale my chcemy przywrócić stary hash i podpis
        block = builder.build()
        block.hash = data["hash"]
        block.extra_data = data.get("extra_data", "")
        
        return block
