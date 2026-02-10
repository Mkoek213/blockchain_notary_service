"""
Testy jednostkowe dla modułu business_logic.

Pokrywają:
- Dokumenty notarialne (SharesTransfer, Resolution, Dividend)
- Factory Method (FinancialActionProvider, GovernanceActionProvider)
- Walidację biznesową (BusinessLogicModule)
- Walidację notarialną (NotaryValidator)
- World State odtwarzany z blockchaina
- Przypadki brzegowe (0 akcji, double spending, odbudowa stanu)
- Integrację end-to-end z blockchain_core
"""

import json
import sys
import os
import pytest

# Ścieżka do blockchain_core
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from blockchain_core import BlockBuilder, Blockchain, Transaction, VotingResult
from blockchain_core.mock_crypto import MockCryptoService

from business_logic import (
    SharesTransfer,
    Resolution,
    Dividend,
    FinancialActionProvider,
    GovernanceActionProvider,
    BusinessLogicModule,
    NotaryValidator,
    SimpleWorldState,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def crypto():
    """MockCryptoService do testów podpisów."""
    return MockCryptoService()


@pytest.fixture
def keys(crypto):
    """Para kluczy (public, private)."""
    return crypto.generate_key_pair()


@pytest.fixture
def world_state():
    """Pusty SimpleWorldState."""
    return SimpleWorldState()


@pytest.fixture
def world_state_with_data():
    """WorldState z przykładowymi danymi."""
    ws = SimpleWorldState()
    ws.register_company("COMP-1", "Example Corp")
    ws.register_company("COMP-2", "Another Corp")
    ws.set_shares("Alice", "COMP-1", 100)
    ws.set_shares("Bob", "COMP-1", 50)
    ws.set_shares("Alice", "COMP-2", 200)
    ws.set_balance("Charlie", 5000.0)
    ws.set_balance("Alice", 10000.0)
    return ws


@pytest.fixture
def blm(world_state_with_data):
    """BusinessLogicModule z gotowym WorldState."""
    return BusinessLogicModule(world_state=world_state_with_data)


@pytest.fixture
def validator(crypto):
    """NotaryValidator z MockCryptoService."""
    return NotaryValidator(crypto_service=crypto)


@pytest.fixture
def financial_provider():
    """FinancialActionProvider."""
    return FinancialActionProvider()


@pytest.fixture
def governance_provider():
    """GovernanceActionProvider."""
    return GovernanceActionProvider()


@pytest.fixture
def blockchain():
    """Świeży Blockchain z genesis block."""
    return Blockchain()


# ============================================================================
# Testy dokumentów notarialnych
# ============================================================================


class TestSharesTransfer:
    """Testy tworzenia i serializacji dokumentu SharesTransfer."""

    def test_create_shares_transfer(self):
        doc = SharesTransfer(
            seller="Alice", buyer="Bob",
            company_id="COMP-1", shares_count=10, price_per_share=50.0,
        )
        assert doc.seller == "Alice"
        assert doc.buyer == "Bob"
        assert doc.shares_count == 10

    def test_to_dict(self):
        doc = SharesTransfer(
            seller="Alice", buyer="Bob",
            company_id="COMP-1", shares_count=10, price_per_share=50.0,
        )
        d = doc.to_dict()
        assert d["type"] == "SharesTransfer"
        assert d["seller"] == "Alice"
        assert d["shares_count"] == 10

    def test_get_json_data_deterministic(self):
        doc = SharesTransfer(
            seller="Alice", buyer="Bob",
            company_id="COMP-1", shares_count=10, price_per_share=50.0,
        )
        json1 = doc.get_json_data()
        json2 = doc.get_json_data()
        assert json1 == json2

    def test_get_json_data_sorted_keys(self):
        doc = SharesTransfer(
            seller="Alice", buyer="Bob",
            company_id="COMP-1", shares_count=10, price_per_share=50.0,
        )
        data = json.loads(doc.get_json_data())
        keys = list(data.keys())
        assert keys == sorted(keys)

    def test_add_and_get_signatures(self):
        doc = SharesTransfer(
            seller="Alice", buyer="Bob",
            company_id="COMP-1", shares_count=10, price_per_share=50.0,
        )
        assert doc.get_signatures() == []
        doc.add_signature("sig_1")
        doc.add_signature("sig_2")
        assert doc.get_signatures() == ["sig_1", "sig_2"]

    def test_get_signatures_returns_copy(self):
        doc = SharesTransfer(
            seller="Alice", buyer="Bob",
            company_id="COMP-1", shares_count=10, price_per_share=50.0,
        )
        doc.add_signature("sig_1")
        sigs = doc.get_signatures()
        sigs.append("hacked")
        assert doc.get_signatures() == ["sig_1"]


class TestResolution:
    """Testy dokumentu Resolution."""

    def test_create_resolution(self):
        doc = Resolution(
            resolution_id="RES-001", company_id="COMP-1",
            resolution_type="budget_approval", votes_for=15, votes_against=3,
        )
        assert doc.resolution_id == "RES-001"
        assert doc.votes_for == 15

    def test_is_passed_true(self):
        doc = Resolution(
            resolution_id="R1", company_id="C1",
            resolution_type="x", votes_for=10, votes_against=3,
        )
        assert doc.is_passed is True

    def test_is_passed_false(self):
        doc = Resolution(
            resolution_id="R1", company_id="C1",
            resolution_type="x", votes_for=3, votes_against=10,
        )
        assert doc.is_passed is False

    def test_is_passed_tie(self):
        doc = Resolution(
            resolution_id="R1", company_id="C1",
            resolution_type="x", votes_for=5, votes_against=5,
        )
        assert doc.is_passed is False

    def test_to_dict(self):
        doc = Resolution(
            resolution_id="R1", company_id="C1",
            resolution_type="budget", votes_for=10, votes_against=2,
        )
        d = doc.to_dict()
        assert d["type"] == "Resolution"
        assert d["resolution_type"] == "budget"


class TestDividend:
    """Testy dokumentu Dividend."""

    def test_create_dividend(self):
        doc = Dividend(
            company_id="COMP-1", amount_per_share=2.5,
            total_amount=25000.0, record_date="2026-01-15",
        )
        assert doc.amount_per_share == 2.5
        assert doc.record_date == "2026-01-15"

    def test_to_dict(self):
        doc = Dividend(
            company_id="C1", amount_per_share=1.0,
            total_amount=1000.0, record_date="2026-06-01",
        )
        d = doc.to_dict()
        assert d["type"] == "Dividend"
        assert d["total_amount"] == 1000.0


# ============================================================================
# Testy Factory Method
# ============================================================================


class TestFinancialActionProvider:
    """Testy fabryki dokumentów finansowych."""

    def test_create_shares_transfer(self, financial_provider):
        doc = financial_provider.create_document({
            "type": "SharesTransfer",
            "seller": "Alice", "buyer": "Bob",
            "company_id": "C1", "shares_count": 10, "price_per_share": 50.0,
        })
        assert isinstance(doc, SharesTransfer)
        assert doc.seller == "Alice"

    def test_create_dividend(self, financial_provider):
        doc = financial_provider.create_document({
            "type": "Dividend",
            "company_id": "C1", "amount_per_share": 2.5,
            "total_amount": 25000.0, "record_date": "2026-01-15",
        })
        assert isinstance(doc, Dividend)

    def test_reject_missing_fields(self, financial_provider):
        with pytest.raises(ValueError):
            financial_provider.create_document({
                "type": "SharesTransfer", "seller": "Alice",
            })

    def test_reject_negative_shares(self, financial_provider):
        with pytest.raises(ValueError):
            financial_provider.create_document({
                "type": "SharesTransfer",
                "seller": "A", "buyer": "B",
                "company_id": "C1", "shares_count": -5, "price_per_share": 10.0,
            })

    def test_reject_same_seller_buyer(self, financial_provider):
        with pytest.raises(ValueError):
            financial_provider.create_document({
                "type": "SharesTransfer",
                "seller": "Alice", "buyer": "Alice",
                "company_id": "C1", "shares_count": 10, "price_per_share": 10.0,
            })

    def test_reject_unsupported_type(self, financial_provider):
        with pytest.raises(ValueError):
            financial_provider.create_document({
                "type": "Resolution",
                "resolution_id": "R1", "company_id": "C1",
                "resolution_type": "x", "votes_for": 10, "votes_against": 3,
            })

    def test_supported_types(self, financial_provider):
        assert "SharesTransfer" in financial_provider.get_supported_types()
        assert "Dividend" in financial_provider.get_supported_types()
        assert "Resolution" not in financial_provider.get_supported_types()


class TestGovernanceActionProvider:
    """Testy fabryki dokumentów zarządczych."""

    def test_create_resolution(self, governance_provider):
        doc = governance_provider.create_document({
            "type": "Resolution",
            "resolution_id": "R1", "company_id": "C1",
            "resolution_type": "budget", "votes_for": 10, "votes_against": 2,
        })
        assert isinstance(doc, Resolution)
        assert doc.resolution_id == "R1"

    def test_reject_missing_fields(self, governance_provider):
        with pytest.raises(ValueError):
            governance_provider.create_document({
                "type": "Resolution", "resolution_id": "R1",
            })

    def test_reject_negative_votes(self, governance_provider):
        with pytest.raises(ValueError):
            governance_provider.create_document({
                "type": "Resolution",
                "resolution_id": "R1", "company_id": "C1",
                "resolution_type": "x", "votes_for": -1, "votes_against": 3,
            })

    def test_reject_unsupported_type(self, governance_provider):
        with pytest.raises(ValueError):
            governance_provider.create_document({
                "type": "SharesTransfer",
                "seller": "A", "buyer": "B",
                "company_id": "C1", "shares_count": 5, "price_per_share": 10.0,
            })

    def test_supported_types(self, governance_provider):
        assert "Resolution" in governance_provider.get_supported_types()
        assert "SharesTransfer" not in governance_provider.get_supported_types()


# ============================================================================
# Testy BusinessLogicModule - przypadki brzegowe
# ============================================================================


class TestValidateSharesTransfer:
    """Testy walidacji transferu udziałów."""

    def test_valid_transfer(self, blm):
        """Alice ma 100 udziałów COMP-1, transfer 30 → OK."""
        assert blm.validate_shares_transfer("Alice", "Bob", 30, "COMP-1") is True

    def test_transfer_all_shares(self, blm):
        """Alice ma 100 udziałów, transfer dokładnie 100 → OK."""
        assert blm.validate_shares_transfer("Alice", "Bob", 100, "COMP-1") is True

    def test_transfer_zero_shares_seller_has_zero(self, blm):
        """
        PRZYPADEK BRZEGOWY: sprzedający ma 0 akcji → odrzucenie.
        Charlie nie ma żadnych udziałów w COMP-1.
        """
        assert blm.validate_shares_transfer("Charlie", "Bob", 10, "COMP-1") is False

    def test_transfer_more_than_owned(self, blm):
        """Alice ma 100, próba transferu 101 → odrzucenie."""
        assert blm.validate_shares_transfer("Alice", "Bob", 101, "COMP-1") is False

    def test_transfer_negative_shares(self, blm):
        """Ujemna liczba udziałów → odrzucenie."""
        assert blm.validate_shares_transfer("Alice", "Bob", -5, "COMP-1") is False

    def test_transfer_zero_shares_count(self, blm):
        """Transfer 0 udziałów → odrzucenie."""
        assert blm.validate_shares_transfer("Alice", "Bob", 0, "COMP-1") is False

    def test_transfer_to_self(self, blm):
        """Transfer do siebie → odrzucenie."""
        assert blm.validate_shares_transfer("Alice", "Alice", 10, "COMP-1") is False

    def test_transfer_nonexistent_company(self, blm):
        """Spółka nie istnieje → odrzucenie."""
        assert blm.validate_shares_transfer("Alice", "Bob", 10, "NIEISTNIEJACA") is False

    def test_transfer_unknown_sender(self, blm):
        """Nieznany użytkownik (brak udziałów) → odrzucenie."""
        assert blm.validate_shares_transfer("Unknown", "Bob", 10, "COMP-1") is False


class TestDoubleSpending:
    """
    PRZYPADEK BRZEGOWY: Double Spending.
    Próba wysłania transakcji o tym samym ID dokumentu dwa razy.
    """

    def test_first_transaction_accepted(self, blm):
        """Pierwsza transakcja z danym ID → akceptacja."""
        tx = {
            "type": "SharesTransfer",
            "seller": "Alice", "buyer": "Bob",
            "company_id": "COMP-1", "shares_count": 10,
            "price_per_share": 50.0,
        }
        result = blm.validate_transaction(tx, None)
        assert result is True

    def test_same_transaction_rejected_second_time(self, blm):
        """
        PRZYPADEK BRZEGOWY: Dokładnie ta sama transakcja wysłana ponownie.
        Pierwszy raz → OK, za drugim razem → double spending → odrzucenie.
        """
        tx = {
            "type": "SharesTransfer",
            "seller": "Alice", "buyer": "Bob",
            "company_id": "COMP-1", "shares_count": 10,
            "price_per_share": 50.0,
        }
        # Rejestrujemy dokument jako przetworzony
        doc_id = blm._compute_document_id(tx)
        blm.world_state.register_document(doc_id)

        # Druga próba → double spending
        result = blm.validate_transaction(tx, None)
        assert result is False

    def test_check_double_spending_known_document(self, blm):
        """check_double_spending zwraca True dla znanego ID."""
        blm.world_state.register_document("known-doc-id")
        assert blm.check_double_spending("known-doc-id") is True

    def test_check_double_spending_unknown_document(self, blm):
        """check_double_spending zwraca False dla nieznanego ID."""
        assert blm.check_double_spending("unknown-doc-id") is False

    def test_double_spending_checked_before_validation(self, blm):
        """
        Double spending jest sprawdzany PRZED walidacją specyficzną.
        Nawet jeśli transakcja byłaby poprawna biznesowo, double spending ją odrzuca.
        """
        tx = {
            "type": "SharesTransfer",
            "seller": "Alice", "buyer": "Bob",
            "company_id": "COMP-1", "shares_count": 5,
            "price_per_share": 10.0,
        }
        # Walidacja biznesowa przeszłaby (Alice ma 100 udziałów)
        assert blm.validate_shares_transfer("Alice", "Bob", 5, "COMP-1") is True

        # Ale rejestrujemy jako przetworzony
        doc_id = blm._compute_document_id(tx)
        blm.world_state.register_document(doc_id)

        # validate_transaction odrzuca mimo poprawności biznesowej
        assert blm.validate_transaction(tx, None) is False


class TestValidateTransaction:
    """Testy validate_transaction dla różnych typów."""

    def test_financial_transaction_valid(self, blm):
        """Transakcja finansowa z wystarczającym saldem → OK."""
        tx = {"type": "Transaction", "sender": "Charlie", "recipient": "Bob", "amount": 1000.0}
        assert blm.validate_transaction(tx, None) is True

    def test_financial_transaction_insufficient_balance(self, blm):
        """Brak wystarczającego salda → odrzucenie."""
        tx = {"type": "Transaction", "sender": "Charlie", "recipient": "Bob", "amount": 99999.0}
        assert blm.validate_transaction(tx, None) is False

    def test_unknown_type_rejected(self, blm):
        """Nieznany typ transakcji → odrzucenie."""
        tx = {"type": "Unknown", "data": "xxx"}
        assert blm.validate_transaction(tx, None) is False

    def test_resolution_valid(self, blm):
        """Uchwała z istniejącą spółką → OK."""
        tx = {
            "type": "Resolution",
            "resolution_id": "R1", "company_id": "COMP-1",
            "resolution_type": "budget", "votes_for": 10, "votes_against": 3,
        }
        assert blm.validate_transaction(tx, None) is True

    def test_resolution_nonexistent_company(self, blm):
        """Uchwała dla nieistniejącej spółki → odrzucenie."""
        tx = {
            "type": "Resolution",
            "resolution_id": "R1", "company_id": "GHOST",
            "resolution_type": "budget", "votes_for": 10, "votes_against": 3,
        }
        assert blm.validate_transaction(tx, None) is False


class TestSmartContract:
    """Testy execute_smart_contract."""

    def test_shares_transfer_approved(self, blm):
        result = blm.execute_smart_contract({
            "contract_type": "shares_transfer",
            "seller": "Alice", "buyer": "Bob",
            "company_id": "COMP-1", "shares_count": 10,
        })
        assert result["status"] == "approved"

    def test_shares_transfer_rejected(self, blm):
        result = blm.execute_smart_contract({
            "contract_type": "shares_transfer",
            "seller": "Alice", "buyer": "Bob",
            "company_id": "COMP-1", "shares_count": 999,
        })
        assert result["status"] == "rejected"
        assert "reason" in result

    def test_unknown_contract_type(self, blm):
        result = blm.execute_smart_contract({"contract_type": "unknown"})
        assert result["status"] == "rejected"


# ============================================================================
# Testy NotaryValidator
# ============================================================================


class TestNotaryValidatorDocument:
    """Testy walidacji strukturalnej dokumentów."""

    def test_valid_shares_transfer(self, validator):
        doc = {
            "type": "SharesTransfer",
            "seller": "A", "buyer": "B",
            "company_id": "C1", "shares_count": 10, "price_per_share": 50.0,
        }
        assert validator.validate_document(doc) is True

    def test_valid_transaction(self, validator):
        doc = {"type": "Transaction", "sender": "A", "recipient": "B", "amount": 100.0}
        assert validator.validate_document(doc) is True

    def test_valid_resolution(self, validator):
        doc = {
            "type": "Resolution", "resolution_id": "R1", "company_id": "C1",
            "resolution_type": "x", "votes_for": 10, "votes_against": 3,
        }
        assert validator.validate_document(doc) is True

    def test_valid_dividend(self, validator):
        doc = {
            "type": "Dividend", "company_id": "C1",
            "amount_per_share": 2.5, "total_amount": 25000.0, "record_date": "2026-01-15",
        }
        assert validator.validate_document(doc) is True

    def test_reject_empty_dict(self, validator):
        assert validator.validate_document({}) is False

    def test_reject_no_type(self, validator):
        assert validator.validate_document({"seller": "A"}) is False

    def test_reject_unknown_type(self, validator):
        assert validator.validate_document({"type": "UNKNOWN"}) is False

    def test_reject_missing_required_fields(self, validator):
        assert validator.validate_document({"type": "SharesTransfer", "seller": "A"}) is False

    def test_reject_not_dict(self, validator):
        assert validator.validate_document("not a dict") is False

    def test_reject_negative_shares(self, validator):
        doc = {
            "type": "SharesTransfer",
            "seller": "A", "buyer": "B",
            "company_id": "C1", "shares_count": -1, "price_per_share": 10.0,
        }
        assert validator.validate_document(doc) is False

    def test_reject_same_sender_recipient(self, validator):
        doc = {"type": "Transaction", "sender": "A", "recipient": "A", "amount": 10.0}
        assert validator.validate_document(doc) is False


class TestNotaryValidatorHash:
    """Testy generowania hasha dokumentu."""

    def test_deterministic_hash(self, validator):
        """Ten sam input → ten sam hash."""
        doc = {"type": "SharesTransfer", "seller": "A", "buyer": "B", "amount": 100}
        hash1 = validator.get_document_hash(doc)
        hash2 = validator.get_document_hash(doc)
        assert hash1 == hash2

    def test_hash_is_sha256(self, validator):
        """Hash ma 64 znaki hex (SHA-256)."""
        doc = {"type": "test"}
        h = validator.get_document_hash(doc)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_different_key_order_same_hash(self, validator):
        """Różna kolejność kluczy → identyczny hash (posortowany JSON)."""
        doc1 = {"type": "X", "a": 1, "b": 2}
        doc2 = {"b": 2, "type": "X", "a": 1}
        assert validator.get_document_hash(doc1) == validator.get_document_hash(doc2)

    def test_different_data_different_hash(self, validator):
        """Różne dane → różny hash."""
        doc1 = {"type": "X", "value": 1}
        doc2 = {"type": "X", "value": 2}
        assert validator.get_document_hash(doc1) != validator.get_document_hash(doc2)


class TestNotaryValidatorSignature:
    """Testy weryfikacji podpisów."""

    def test_verify_with_crypto_service(self, validator, crypto, keys):
        """Weryfikacja podpisu przez CryptoService."""
        pub, priv = keys
        doc_data = {"test": "data", "value": 42}
        signature = crypto.sign_block(doc_data, priv)
        # MockCrypto: verify używa pub jako klucza (symetryczne mock)
        assert validator.verify_signature(doc_data, signature, pub) is True

    def test_verify_wrong_signature(self, validator, keys):
        """Błędny podpis → False."""
        pub, _ = keys
        assert validator.verify_signature({"data": 1}, "wrong_sig", pub) is False

    def test_verify_without_crypto_service(self):
        """Brak CryptoService → zawsze False."""
        val = NotaryValidator(crypto_service=None)
        assert val.verify_signature({"x": 1}, "sig", "key") is False

    def test_verify_empty_signature(self, validator, keys):
        """Pusty podpis → False."""
        pub, _ = keys
        assert validator.verify_signature({"x": 1}, "", pub) is False

    def test_verify_empty_key(self, validator):
        """Pusty klucz publiczny → False."""
        assert validator.verify_signature({"x": 1}, "sig", "") is False


# ============================================================================
# Testy World State - odbudowa z blockchaina
# ============================================================================


class TestWorldStateBuildFromBlockchain:
    """
    PRZYPADEK BRZEGOWY: Poprawność odbudowy WorldState
    po dodaniu kilku różnych bloków.
    """

    def test_rebuild_shares_from_multiple_blocks(self, blockchain, crypto, keys):
        """
        Dodanie kilku bloków z transferami udziałów →
        WorldState poprawnie oblicza wynikowy stan.
        """
        pub, priv = keys
        fp = FinancialActionProvider()

        # Blok 1: Alice → Bob: 30 udziałów
        doc1 = fp.create_document({
            "type": "SharesTransfer",
            "seller": "Alice", "buyer": "Bob",
            "company_id": "CORP-A", "shares_count": 30, "price_per_share": 10.0,
        })
        block1 = (BlockBuilder()
            .set_parent_hash(blockchain.get_last_block().get_hash())
            .set_author("notary")
            .add_document(doc1)
            .build(crypto, priv))
        blockchain.append_block(block1)

        # Blok 2: Alice → Charlie: 20 udziałów
        doc2 = fp.create_document({
            "type": "SharesTransfer",
            "seller": "Alice", "buyer": "Charlie",
            "company_id": "CORP-A", "shares_count": 20, "price_per_share": 15.0,
        })
        block2 = (BlockBuilder()
            .set_parent_hash(blockchain.get_last_block().get_hash())
            .set_author("notary")
            .add_document(doc2)
            .build(crypto, priv))
        blockchain.append_block(block2)

        # Blok 3: Bob → Charlie: 10 udziałów
        doc3 = fp.create_document({
            "type": "SharesTransfer",
            "seller": "Bob", "buyer": "Charlie",
            "company_id": "CORP-A", "shares_count": 10, "price_per_share": 20.0,
        })
        block3 = (BlockBuilder()
            .set_parent_hash(blockchain.get_last_block().get_hash())
            .set_author("notary")
            .add_document(doc3)
            .build(crypto, priv))
        blockchain.append_block(block3)

        # Odbuduj WorldState
        ws = SimpleWorldState()
        ws.build_from_blockchain(blockchain)

        # Alice: -30 -20 = -50 udziałów (od stanu startowego 0)
        assert ws.get_shares("Alice", "CORP-A") == -50
        # Bob: +30 -10 = 20 udziałów
        assert ws.get_shares("Bob", "CORP-A") == 20
        # Charlie: +20 +10 = 30 udziałów
        assert ws.get_shares("Charlie", "CORP-A") == 30

    def test_rebuild_balances(self, blockchain, crypto, keys):
        """WorldState poprawnie oblicza salda po transferach."""
        pub, priv = keys
        fp = FinancialActionProvider()

        doc = fp.create_document({
            "type": "SharesTransfer",
            "seller": "Seller", "buyer": "Buyer",
            "company_id": "CORP-X", "shares_count": 50, "price_per_share": 20.0,
        })
        block = (BlockBuilder()
            .set_parent_hash(blockchain.get_last_block().get_hash())
            .set_author("notary")
            .add_document(doc)
            .build(crypto, priv))
        blockchain.append_block(block)

        ws = SimpleWorldState()
        ws.build_from_blockchain(blockchain)

        # Seller otrzymał: 50 * 20 = 1000
        assert ws.get_balance("Seller") == 1000.0
        # Buyer zapłacił: -1000
        assert ws.get_balance("Buyer") == -1000.0

    def test_rebuild_tracks_processed_documents(self, blockchain, crypto, keys):
        """WorldState rejestruje przetworzone dokumenty (double spending check)."""
        pub, priv = keys
        fp = FinancialActionProvider()

        doc = fp.create_document({
            "type": "SharesTransfer",
            "seller": "A", "buyer": "B",
            "company_id": "C1", "shares_count": 5, "price_per_share": 10.0,
        })
        block = (BlockBuilder()
            .set_parent_hash(blockchain.get_last_block().get_hash())
            .set_author("notary")
            .add_document(doc)
            .build(crypto, priv))
        blockchain.append_block(block)

        ws = SimpleWorldState()
        ws.build_from_blockchain(blockchain)

        # Powinien być 1 przetworzony dokument
        assert len(ws._processed_documents) == 1

    def test_rebuild_mixed_document_types(self, blockchain, crypto, keys):
        """WorldState poprawnie przetwarza różne typy dokumentów w jednym bloku."""
        pub, priv = keys
        fp = FinancialActionProvider()
        gp = GovernanceActionProvider()

        shares_doc = fp.create_document({
            "type": "SharesTransfer",
            "seller": "A", "buyer": "B",
            "company_id": "C1", "shares_count": 10, "price_per_share": 5.0,
        })
        resolution_doc = gp.create_document({
            "type": "Resolution",
            "resolution_id": "R1", "company_id": "C1",
            "resolution_type": "budget", "votes_for": 15, "votes_against": 2,
        })

        # Oba dokumenty w jednym bloku
        block = (BlockBuilder()
            .set_parent_hash(blockchain.get_last_block().get_hash())
            .set_author("notary")
            .add_document(shares_doc)
            .add_document(resolution_doc)
            .build(crypto, priv))
        blockchain.append_block(block)

        ws = SimpleWorldState()
        ws.build_from_blockchain(blockchain)

        assert ws.get_shares("B", "C1") == 10
        assert len(ws._processed_documents) == 2

    def test_rebuild_resets_previous_state(self, blockchain, crypto, keys):
        """build_from_blockchain resetuje poprzedni stan przed odbudową."""
        pub, priv = keys
        fp = FinancialActionProvider()

        doc = fp.create_document({
            "type": "SharesTransfer",
            "seller": "X", "buyer": "Y",
            "company_id": "C1", "shares_count": 5, "price_per_share": 10.0,
        })
        block = (BlockBuilder()
            .set_parent_hash(blockchain.get_last_block().get_hash())
            .set_author("notary")
            .add_document(doc)
            .build(crypto, priv))
        blockchain.append_block(block)

        ws = SimpleWorldState()
        # Ustawiamy sztuczne dane
        ws.set_shares("STARY", "C1", 9999)

        # Odbudowa powinna zresetować
        ws.build_from_blockchain(blockchain)

        assert ws.get_shares("STARY", "C1") == 0
        assert ws.get_shares("Y", "C1") == 5

    def test_rebuild_empty_blockchain_only_genesis(self, blockchain):
        """Blockchain z samym genesis → pusty WorldState."""
        ws = SimpleWorldState()
        ws.build_from_blockchain(blockchain)

        assert ws.get_shares("anyone", "C1") == 0
        assert ws.get_balance("anyone") == 0.0
        assert len(ws._processed_documents) == 0

    def test_rebuild_dividend_distribution(self, blockchain, crypto, keys):
        """WorldState poprawnie oblicza wypłatę dywidendy do udziałowców."""
        pub, priv = keys
        fp = FinancialActionProvider()

        # Blok 1: Transfer udziałów do dwóch osób
        doc1 = fp.create_document({
            "type": "SharesTransfer",
            "seller": "Founder", "buyer": "InvestorA",
            "company_id": "C1", "shares_count": 100, "price_per_share": 1.0,
        })
        doc2 = fp.create_document({
            "type": "SharesTransfer",
            "seller": "Founder", "buyer": "InvestorB",
            "company_id": "C1", "shares_count": 50, "price_per_share": 1.0,
        })
        block1 = (BlockBuilder()
            .set_parent_hash(blockchain.get_last_block().get_hash())
            .set_author("notary")
            .add_document(doc1)
            .add_document(doc2)
            .build(crypto, priv))
        blockchain.append_block(block1)

        # Blok 2: Dywidenda 3.0 PLN / udział
        div = fp.create_document({
            "type": "Dividend",
            "company_id": "C1", "amount_per_share": 3.0,
            "total_amount": 450.0, "record_date": "2026-06-01",
        })
        block2 = (BlockBuilder()
            .set_parent_hash(blockchain.get_last_block().get_hash())
            .set_author("notary")
            .add_document(div)
            .build(crypto, priv))
        blockchain.append_block(block2)

        ws = SimpleWorldState()
        ws.build_from_blockchain(blockchain)

        # InvestorA: 100 udziałów * 3.0 = 300.0 dywidendy
        # Plus saldo z zakupu: -100 (100 * 1.0)
        assert ws.get_balance("InvestorA") == -100.0 + 300.0  # 200.0

        # InvestorB: 50 udziałów * 3.0 = 150.0 dywidendy
        # Plus saldo z zakupu: -50 (50 * 1.0)
        assert ws.get_balance("InvestorB") == -50.0 + 150.0  # 100.0


# ============================================================================
# Test integracji end-to-end
# ============================================================================


class TestEndToEndIntegration:
    """Pełna integracja: fabryka → walidacja → blok → blockchain → WorldState."""

    def test_full_flow(self, crypto, keys):
        """
        Pełny przepływ biznesowy:
        1. Tworzy dokumenty przez Factory
        2. Waliduje przez BusinessLogicModule
        3. Buduje blok przez BlockBuilder
        4. Dodaje do Blockchain
        5. Odbudowuje WorldState → stan odzwierciedla zmiany
        """
        pub, priv = keys
        blockchain = Blockchain()

        # Setup: WorldState z początkowymi udziałami
        ws = SimpleWorldState()
        ws.register_company("CORP", "Test Corp")
        ws.set_shares("Seller", "CORP", 100)
        blm = BusinessLogicModule(world_state=ws)

        # 1. Tworzenie dokumentu przez Factory
        fp = FinancialActionProvider()
        doc = fp.create_document({
            "type": "SharesTransfer",
            "seller": "Seller", "buyer": "Buyer",
            "company_id": "CORP", "shares_count": 40, "price_per_share": 100.0,
        })

        # 2. Walidacja biznesowa
        tx_data = doc.to_dict()
        assert blm.validate_transaction(tx_data, None) is True

        # 3. Budowanie bloku
        block = (BlockBuilder()
            .set_parent_hash(blockchain.get_last_block().get_hash())
            .set_author("notary_1")
            .add_document(doc)
            .build(crypto, priv))

        # 4. Dodanie do blockchain
        assert blockchain.append_block(block) is True
        assert blockchain.get_height() == 2

        # 5. Odbudowa WorldState z blockchaina
        fresh_ws = SimpleWorldState()
        fresh_ws.build_from_blockchain(blockchain)

        assert fresh_ws.get_shares("Buyer", "CORP") == 40
        assert fresh_ws.get_shares("Seller", "CORP") == -40
        assert fresh_ws.get_balance("Seller") == 4000.0   # 40 * 100
        assert fresh_ws.get_balance("Buyer") == -4000.0

        # Weryfikacja podpisu bloku
        assert block.validate_signature(pub, crypto) is True
