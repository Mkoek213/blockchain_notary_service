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
