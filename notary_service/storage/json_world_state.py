import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from blockchain_core.interfaces import IWorldStateManager
from business_logic.world_state import SimpleWorldState
from notary_service.block_codec import block_from_dict

from .json_ledger import JsonLedgerRepository


class JsonWorldStateManager(SimpleWorldState, IWorldStateManager):
    """World State z persystencją do pliku JSON."""

    def __init__(
        self,
        path: str = "data/world_state.json",
        ledger_repository: Optional[JsonLedgerRepository] = None,
    ) -> None:
        super().__init__()
        self.path = path
        self.ledger_repository = ledger_repository

    def update_state(self, block: Any) -> bool:
        try:
            self._process_block(block)
            return True
        except Exception:
            return False

    def rollback_to_height(self, height: int) -> bool:
        if self.ledger_repository is None:
            return False
        blocks = self.ledger_repository.get_full_chain()
        if height < 0 or height > len(blocks):
            return False
        self._balances.clear()
        self._shares.clear()
        self._companies.clear()
        self._processed_documents.clear()

        # Zakładamy, że indeks 0 to genesis (bez dokumentów)
        for block_data in blocks[1:height]:
            block = block_from_dict(block_data)
            if block is None:
                continue
            self._process_block(block)
        self.save()
        return True

    def get_state_root(self) -> str:
        state = self.export_state()
        data = json.dumps(state, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def export_state(self) -> Dict[str, Any]:
        shares_list: List[Dict[str, Any]] = []
        for (account_id, company_id), count in self._shares.items():
            shares_list.append(
                {
                    "account_id": account_id,
                    "company_id": company_id,
                    "shares": count,
                }
            )
        return {
            "balances": dict(self._balances),
            "shares": shares_list,
            "companies": dict(self._companies),
            "processed_documents": sorted(self._processed_documents),
        }

    def import_state(self, state: Dict[str, Any]) -> None:
        self._balances = dict(state.get("balances", {}))
        self._companies = dict(state.get("companies", {}))
        self._processed_documents = set(state.get("processed_documents", []))
        self._shares = {}
        for entry in state.get("shares", []):
            key = (entry.get("account_id"), entry.get("company_id"))
            self._shares[key] = int(entry.get("shares", 0))

    def load(self) -> bool:
        if not os.path.exists(self.path):
            return False
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                state = json.load(f)
            if not isinstance(state, dict):
                return False
            self.import_state(state)
            return True
        except Exception:
            return False

    def save(self) -> bool:
        try:
            directory = os.path.dirname(self.path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            tmp_path = f"{self.path}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self.export_state(), f, sort_keys=True, indent=2, ensure_ascii=True)
            os.replace(tmp_path, self.path)
            return True
        except Exception:
            return False
