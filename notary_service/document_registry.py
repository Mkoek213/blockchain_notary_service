from typing import Any, Dict, List, Optional

from blockchain_core.notarial_document import NotarialDocument, Transaction, VotingResult
from business_logic.document_providers import (
    DocumentProvider,
    FinancialActionProvider,
    GovernanceActionProvider,
)
from notary_service.block_codec import GenericNotarialDocument


class DocumentRegistry:
    """Router po dostawcach dokumentów (Factory Method)."""

    def __init__(self, providers: Optional[List[DocumentProvider]] = None) -> None:
        if providers is None:
            providers = [FinancialActionProvider(), GovernanceActionProvider()]
        self.providers = providers

    def create_document(self, document_data: Dict[str, Any]) -> NotarialDocument:
        # Preserve extra fields like document_id by using generic document.
        if document_data.get("document_id") is not None:
            return GenericNotarialDocument(document_data)
        doc_type = document_data.get("type")
        if doc_type:
            for provider in self.providers:
                try:
                    if doc_type in provider.get_supported_types():
                        return provider.create_document(document_data)
                except Exception:
                    continue

        if doc_type == "Transaction":
            tx_doc = Transaction(
                sender=document_data["sender"],
                recipient=document_data["recipient"],
                amount=document_data["amount"],
            )
            for sig in document_data.get("signatures", []):
                tx_doc.add_signature(sig)
            return tx_doc
        if doc_type == "VotingResult":
            voting_doc = VotingResult(
                voting_id=document_data["voting_id"],
                results=document_data["results"],
            )
            for sig in document_data.get("signatures", []):
                voting_doc.add_signature(sig)
            return voting_doc

        return GenericNotarialDocument(document_data)
