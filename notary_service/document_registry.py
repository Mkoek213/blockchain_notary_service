from typing import Any, Dict, List, Optional

from blockchain_core.notarial_document import NotarialDocument
from business_logic.document_providers import (
    DocumentProvider,
    FinancialActionProvider,
    GovernanceActionProvider,
)
from notary_service.block_codec import GenericNotarialDocument


class DocumentRegistry:
    """Router po dostawcach dokumentów (Factory Method).

    Deleguje tworzenie dokumentów do zarejestrowanych providerów,
    eliminując centralne struktury kontrolne typu switch-case
    (zgodnie z zasadą Open/Closed).
    """

    def __init__(self, providers: Optional[List[DocumentProvider]] = None) -> None:
        if providers is None:
            providers = [FinancialActionProvider(), GovernanceActionProvider()]
        self.providers = providers

    def create_document(self, document_data: Dict[str, Any]) -> NotarialDocument:
        """Tworzy dokument używając zarejestrowanych providerów (Factory Method).

        Kolejność:
        1. Delegacja do Factory Method providerów
        2. Fallback: GenericNotarialDocument (zachowuje pełne dane JSON)
        """
        doc_type = document_data.get("type")

        # --- Factory Method: delegacja do odpowiedniego providera ---
        if doc_type:
            for provider in self.providers:
                try:
                    if doc_type in provider.get_supported_types():
                        return provider.create_document(document_data)
                except Exception:
                    continue

        # --- Fallback: GenericNotarialDocument zachowuje wszystkie dane ---
        return GenericNotarialDocument(document_data)
