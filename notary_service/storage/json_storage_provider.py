from typing import Any, Dict, List, Optional, cast

from blockchain_core.interfaces import IStorageProvider

from .json_ledger import JsonLedgerRepository


class JsonStorageProvider(IStorageProvider):
    """Adapter IStorageProvider wykorzystujący JsonLedgerRepository."""

    def __init__(self, ledger_path: str = "data/ledger.json") -> None:
        self.ledger = JsonLedgerRepository(ledger_path)

    def save_block(self, block_data: Dict[str, Any]) -> bool:
        return self.ledger.append_block(block_data)

    def load_blockchain(self) -> Optional[List[Dict[str, Any]]]:
        return self.ledger.get_full_chain()

    def get_block_by_hash(self, block_hash: str) -> Optional[Dict[str, Any]]:
        block = self.ledger.get_block_by_hash(block_hash)
        if block is None:
            return None
        return cast(Dict[str, Any], block)

    def replace_chain(self, blocks: List[Dict[str, Any]]) -> bool:
        return self.ledger.replace_chain(blocks)
