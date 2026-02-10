"""
Business Logic Module
=====================
Moduł logiki biznesowej dla systemu notarialnego blockchain.

Wzorce projektowe:
    - Factory Method: DocumentProvider → FinancialActionProvider / GovernanceActionProvider
    - Dependency Injection: BusinessLogicModule przyjmuje WorldState przez konstruktor

Dokumenty notarialne:
    - SharesTransfer: transfer udziałów w spółce
    - Resolution: uchwała / wynik głosowania
    - Dividend: wypłata dywidendy

Walidacja:
    - BusinessLogicModule: reguły biznesowe (double spending, salda, udziały)
    - NotaryValidator: walidacja strukturalna + weryfikacja podpisów (PoA/X.509)

Stan świata:
    - SimpleWorldState: odtwarzany z łańcucha bloków
"""

from .documents import Dividend, Resolution, SharesTransfer
from .document_providers import (
    DocumentProvider,
    FinancialActionProvider,
    GovernanceActionProvider,
)
from .business_logic_module import BusinessLogicModule
from .notary_validator import NotaryValidator
from .world_state import SimpleWorldState

__all__ = [
    # Dokumenty notarialne (produkty Factory Method)
    "SharesTransfer",
    "Resolution",
    "Dividend",
    # Factory Method - providery dokumentów
    "DocumentProvider",
    "FinancialActionProvider",
    "GovernanceActionProvider",
    # Walidacja biznesowa
    "BusinessLogicModule",
    # Walidacja notarialna + podpisy
    "NotaryValidator",
    # World State
    "SimpleWorldState",
]
