import json
from typing import Any, Dict, List, Optional

from blockchain_core.block_builder import Block, BlockBuilder
from blockchain_core.notarial_document import NotarialDocument


class GenericNotarialDocument(NotarialDocument):
    """Uniwersalny dokument notarialny zachowujący pełne dane JSON."""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def get_json_data(self) -> str:
        return json.dumps(self._data, sort_keys=True)

    def get_signatures(self) -> List[str]:
        signatures = self._data.get("signatures", [])
        return list(signatures)


def document_from_dict(data: Dict[str, Any]) -> NotarialDocument:
    """Odtwarza dokument ze słownika jako GenericNotarialDocument.

    Nie stosuje switch-case — wszystkie dane są zachowane w formacie JSON,
    co pozwala na ich poprawne przetworzenie przez WorldState i inne moduły.
    """
    return GenericNotarialDocument(data)


def block_from_dict(block_data: Dict[str, Any]) -> Optional[Block]:
    try:
        builder = BlockBuilder()
        builder.set_parent_hash(block_data["previous_hash"])
        builder.set_author(block_data["miner"])
        builder.set_timestamp(block_data["timestamp"])
        builder.set_roots(
            block_data.get("transactions_root", ""),
            block_data.get("state_root", ""),
        )
        for doc_data in block_data.get("documents", []):
            builder.add_document(document_from_dict(doc_data))
        builder._extra_data = block_data.get("extra_data", "")
        block = builder.build()
        expected_hash = block_data.get("hash")
        if expected_hash and expected_hash != block.get_hash():
            return None
        return block
    except Exception:
        return None
