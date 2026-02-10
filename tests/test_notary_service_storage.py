from blockchain_core import BlockBuilder, Transaction
from business_logic.documents import SharesTransfer
from notary_service.storage import JsonLedgerRepository, JsonWorldStateManager


def build_block(parent_hash: str, doc):
    builder = BlockBuilder()
    builder.set_parent_hash(parent_hash)
    builder.set_author("miner")
    if doc is not None:
        builder.add_document(doc)
    return builder.build()


def test_json_ledger_roundtrip(tmp_path):
    ledger_path = tmp_path / "ledger.json"
    ledger = JsonLedgerRepository(str(ledger_path))

    tx = Transaction("Alice", "Bob", 5.0)
    block = build_block("0", tx)
    assert ledger.append_block(block) is True

    assert ledger.get_block_by_hash(block.get_hash()) is not None
    ledger2 = JsonLedgerRepository(str(ledger_path))
    chain = ledger2.get_full_chain()
    assert len(chain) == 1
    assert chain[0]["hash"] == block.get_hash()


def test_world_state_update_save_load(tmp_path):
    state_path = tmp_path / "world_state.json"
    ws = JsonWorldStateManager(str(state_path))
    ws.register_company("COMP-1", "Example")
    ws.set_shares("Alice", "COMP-1", 10)

    doc = SharesTransfer(
        seller="Alice",
        buyer="Bob",
        company_id="COMP-1",
        shares_count=5,
        price_per_share=1.0,
    )
    block = build_block("0", doc)
    assert ws.update_state(block) is True
    assert ws.get_shares("Alice", "COMP-1") == 5
    assert ws.get_shares("Bob", "COMP-1") == 5

    assert ws.save() is True

    ws2 = JsonWorldStateManager(str(state_path))
    assert ws2.load() is True
    assert ws2.get_shares("Alice", "COMP-1") == 5
    assert ws2.get_shares("Bob", "COMP-1") == 5

    root = ws2.get_state_root()
    assert isinstance(root, str)
    assert len(root) == 64


def test_world_state_rollback(tmp_path):
    ledger_path = tmp_path / "ledger.json"
    state_path = tmp_path / "world_state.json"
    ledger = JsonLedgerRepository(str(ledger_path))

    genesis = build_block("0", None)
    ledger.append_block(genesis)

    doc = SharesTransfer(
        seller="Alice",
        buyer="Bob",
        company_id="COMP-1",
        shares_count=5,
        price_per_share=1.0,
    )
    block = build_block(genesis.get_hash(), doc)
    ledger.append_block(block)

    ws = JsonWorldStateManager(str(state_path), ledger_repository=ledger)
    assert ws.rollback_to_height(1) is True
    assert ws.get_shares("Alice", "COMP-1") == 0
    assert ws.get_shares("Bob", "COMP-1") == 0
