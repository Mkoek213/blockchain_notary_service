import json
import os
from typing import Any, Dict, List, Optional

from blockchain_core.interfaces import ILedgerRepository


class JsonLedgerRepository(ILedgerRepository):
    """Plikowy ledger oparty o JSON (lista bloków jako dict)."""

    def __init__(self, path: str = "data/ledger.json") -> None:
        self.path = path
        self._blocks: List[Dict[str, Any]] = []
        self._blocks = self._load_from_disk()

    def append_block(self, block: Any) -> bool:
        try:
            block_data = block.to_dict() if hasattr(block, "to_dict") else dict(block)
            self._blocks.append(block_data)
            self._write_blocks()
            return True
        except Exception:
            return False

    def get_block_by_height(self, height: int) -> Optional[Any]:
        if height < 0 or height >= len(self._blocks):
            return None
        return self._blocks[height]

    def get_block_by_hash(self, block_hash: str) -> Optional[Any]:
        for block in self._blocks:
            if block.get("hash") == block_hash:
                return block
        return None

    def get_full_chain(self) -> List[Any]:
        return list(self._blocks)

    def _load_from_disk(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.path):
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except Exception:
            return []
        return []

    def _write_blocks(self) -> None:
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        tmp_path = f"{self.path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self._blocks, f, sort_keys=True, indent=2, ensure_ascii=True)
        os.replace(tmp_path, self.path)
