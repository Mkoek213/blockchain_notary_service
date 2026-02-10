from notary_service import NotaryService


def main() -> None:
    # In-memory demo (bez PKI i bez sieci)
    service = NotaryService(use_storage=False)

    # Inicjalizacja stanu świata
    service.world_state.register_company("COMP-1", "Example Corp")
    service.world_state.set_shares("Alice", "COMP-1", 100)
    service.world_state.set_shares("Bob", "COMP-1", 0)

    # Dane dokumentu (SharesTransfer)
    doc_data = {
        "type": "SharesTransfer",
        "seller": "Alice",
        "buyer": "Bob",
        "company_id": "COMP-1",
        "shares_count": 10,
        "price_per_share": 50.0,
        "signatures": [],
    }

    doc = service.create_document(doc_data)
    is_valid = service.validate_document(doc_data)
    print(f"Document valid: {is_valid}")

    if not is_valid:
        return

    block = service.build_block(author="notary-1", documents=[doc])
    added = service.add_block(block)
    print(f"Block added: {added}")

    # Stan po aktualizacji
    print("Alice shares:", service.world_state.get_shares("Alice", "COMP-1"))
    print("Bob shares:", service.world_state.get_shares("Bob", "COMP-1"))

    # Opcjonalnie: Storage
    # service = NotaryService(use_storage=True, data_dir="data")


if __name__ == "__main__":
    main()
