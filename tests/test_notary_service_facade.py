from business_logic.documents import SharesTransfer
from notary_service import NotaryService


def test_facade_create_validate_and_add_block():
    service = NotaryService(use_storage=False)
    service.world_state.register_company("COMP-1", "Example")
    service.world_state.set_shares("Alice", "COMP-1", 100)
    service.world_state.set_shares("Bob", "COMP-1", 0)

    doc_data = {
        "type": "SharesTransfer",
        "seller": "Alice",
        "buyer": "Bob",
        "company_id": "COMP-1",
        "shares_count": 10,
        "price_per_share": 1.0,
        "signatures": [],
    }

    doc = service.create_document(doc_data)
    assert isinstance(doc, SharesTransfer)

    assert service.validate_document(doc_data) is True

    block = service.build_block(author="notary-1", documents=[doc])
    assert service.add_block(block) is True

    assert service.world_state.get_shares("Alice", "COMP-1") == 90
    assert service.world_state.get_shares("Bob", "COMP-1") == 10
    assert service.blockchain.get_height() == 2


def test_transfer_rejects_negative_shares():
    """Transfer z ujemną liczbą udziałów powinien być odrzucony."""
    service = NotaryService(use_storage=False)
    service.world_state.register_company("COMP-1", "Example")
    service.world_state.set_shares("Alice", "COMP-1", 100)

    doc_data = {
        "type": "SharesTransfer",
        "seller": "Alice",
        "buyer": "Bob",
        "company_id": "COMP-1",
        "shares_count": -5,
        "price_per_share": 1.0,
        "signatures": [],
    }

    assert service.validate_document(doc_data) is False
    # Udziały Alice powinny pozostać niezmienione
    assert service.world_state.get_shares("Alice", "COMP-1") == 100


def test_transfer_rejects_insufficient_shares():
    """Transfer większej liczby udziałów niż posiada sprzedający powinien być odrzucony."""
    service = NotaryService(use_storage=False)
    service.world_state.register_company("COMP-1", "Example")
    service.world_state.set_shares("Alice", "COMP-1", 50)
    service.world_state.set_shares("Bob", "COMP-1", 0)

    doc_data = {
        "type": "SharesTransfer",
        "seller": "Alice",
        "buyer": "Bob",
        "company_id": "COMP-1",
        "shares_count": 200,
        "price_per_share": 1.0,
        "signatures": [],
    }

    assert service.validate_document(doc_data) is False
    # Udziały nie powinny się zmienić
    assert service.world_state.get_shares("Alice", "COMP-1") == 50
    assert service.world_state.get_shares("Bob", "COMP-1") == 0


def test_world_state_no_negative_after_transfer():
    """World State nie powinien dopuścić do ujemnego stanu udziałów."""
    from business_logic.world_state import SimpleWorldState

    ws = SimpleWorldState()
    ws.register_company("COMP-1", "Example")
    ws.set_shares("Alice", "COMP-1", 10)

    # Próba transferu większej liczby udziałów niż posiada
    ws._apply_shares_transfer({
        "seller": "Alice",
        "buyer": "Bob",
        "company_id": "COMP-1",
        "shares_count": 20,
        "price_per_share": 1.0,
    })

    # Guard powinien zapobiec ujemnemu stanowi
    assert ws.get_shares("Alice", "COMP-1") == 10  # Bez zmian
    assert ws.get_shares("Bob", "COMP-1") == 0  # Bez zmian

    # Próba transferu ujemnej liczby
    ws._apply_shares_transfer({
        "seller": "Alice",
        "buyer": "Bob",
        "company_id": "COMP-1",
        "shares_count": -5,
        "price_per_share": 1.0,
    })

    assert ws.get_shares("Alice", "COMP-1") == 10  # Bez zmian
    assert ws.get_shares("Bob", "COMP-1") == 0  # Bez zmian
