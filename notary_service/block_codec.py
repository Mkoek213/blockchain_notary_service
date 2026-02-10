import json
from typing import Any, Dict, List, Optional

from blockchain_core.block_builder import Block, BlockBuilder
from blockchain_core.notarial_document import NotarialDocument, Transaction, VotingResult
from business_logic.documents import Dividend, Resolution, SharesTransfer


class GenericNotarialDocument(NotarialDocument):
    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def get_json_data(self) -> str:
        return json.dumps(self._data, sort_keys=True)

    def get_signatures(self) -> List[str]:
        signatures = self._data.get("signatures", [])
        return list(signatures)


def document_from_dict(data: Dict[str, Any]) -> NotarialDocument:
    doc_type = data.get("type")
    if data.get("document_id") is not None:
        return GenericNotarialDocument(data)
    try:
        if doc_type == "SharesTransfer":
            shares_doc = SharesTransfer(
                seller=data["seller"],
                buyer=data["buyer"],
                company_id=data["company_id"],
                shares_count=data["shares_count"],
                price_per_share=data.get("price_per_share", 0.0),
            )
            for sig in data.get("signatures", []):
                shares_doc.add_signature(sig)
            return shares_doc
        if doc_type == "Resolution":
            resolution_doc = Resolution(
                resolution_id=data["resolution_id"],
                company_id=data["company_id"],
                resolution_type=data["resolution_type"],
                votes_for=data["votes_for"],
                votes_against=data["votes_against"],
            )
            for sig in data.get("signatures", []):
                resolution_doc.add_signature(sig)
            return resolution_doc
        if doc_type == "Dividend":
            dividend_doc = Dividend(
                company_id=data["company_id"],
                amount_per_share=data["amount_per_share"],
                total_amount=data["total_amount"],
                record_date=data["record_date"],
            )
            for sig in data.get("signatures", []):
                dividend_doc.add_signature(sig)
            return dividend_doc
        if doc_type == "Transaction":
            tx_doc = Transaction(
                sender=data["sender"],
                recipient=data["recipient"],
                amount=data["amount"],
            )
            for sig in data.get("signatures", []):
                tx_doc.add_signature(sig)
            return tx_doc
        if doc_type == "VotingResult":
            voting_doc = VotingResult(voting_id=data["voting_id"], results=data["results"])
            for sig in data.get("signatures", []):
                voting_doc.add_signature(sig)
            return voting_doc
    except Exception:
        # Fallback to generic document
        return GenericNotarialDocument(data)

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
