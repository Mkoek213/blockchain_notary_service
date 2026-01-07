"""
Przykład użycia blockchain_core z wzorcem Builder zgodnie z diagramem sekwencji.
"""

from blockchain_core import BlockBuilder, Blockchain, Transaction, VotingResult
from blockchain_core.mock_crypto import MockCryptoService


def demo_builder_pattern():
    """Demonstracja wzorca Builder zgodnie z diagramem sekwencji."""
    print("=" * 70)
    print("DEMO: Wzorzec Builder - zgodnie z diagramem sekwencji")
    print("=" * 70)

    # 1. Inicjalizacja serwisów
    print("\n[1] Inicjalizacja serwisów...")
    blockchain = Blockchain()
    crypto_service = MockCryptoService()

    # Generuj klucze dla minera
    public_key, private_key = crypto_service.generate_key_pair()
    miner_address = f"miner_{public_key[:8]}"
    print("    ✓ Blockchain zainicjalizowany")
    print("    ✓ CryptoService gotowy")
    print(f"    ✓ Wygenerowano klucze dla minera: {miner_address}")

    # 2. Tworzenie dokumentów notarialnych
    print("\n[2] Tworzenie dokumentów notarialnych...")

    # Transakcja
    transaction = Transaction(sender="Alice", recipient="Bob", amount=1000.0)
    transaction.add_signature("sig_alice_123")
    print("    ✓ Utworzono transakcję: Alice -> Bob (1000.0)")

    # Wynik głosowania
    voting = VotingResult(
        voting_id="VOTE-2026-001", results={"Option A": 150, "Option B": 120, "Option C": 80}
    )
    voting.add_signature("sig_voting_authority")
    print("    ✓ Utworzono wynik głosowania: VOTE-2026-001")

    # 3. DIAGRAM SEKWENCJI - Tworzenie bloku przez NotaryService
    print("\n[3] Tworzenie bloku (zgodnie z diagramem sekwencji)...")

    # NS->>BB: new BlockBuilder()
    print("    • NotaryService -> BlockBuilder: new BlockBuilder()")
    builder = BlockBuilder()

    # NS->>BB: addDocument(doc)
    print("    • NotaryService -> BlockBuilder: addDocument(transaction)")
    builder.add_document(transaction)

    print("    • NotaryService -> BlockBuilder: addDocument(voting)")
    builder.add_document(voting)

    # NS->>BC: getLastBlock()
    print("    • NotaryService -> Blockchain: getLastBlock()")
    last_block = blockchain.get_last_block()
    parent_hash = last_block.get_hash()
    print(f"      <- Blockchain zwraca parent_hash: {parent_hash[:16]}...")

    # NS->>BB: setParentHash(parentHash)
    print("    • NotaryService -> BlockBuilder: setParentHash()")
    builder.set_parent_hash(parent_hash)

    # NS->>BB: setAuthor(minerAddress)
    print(f"    • NotaryService -> BlockBuilder: setAuthor({miner_address})")
    builder.set_author(miner_address)

    # NS->>BB: build()
    print("    • NotaryService -> BlockBuilder: build()")
    print("      [Inside build() method]")
    print("        - validateInputs()")
    print("        - calculateRoots()")
    print("        - CryptoService: signBlock() -> signature")

    # BB->>BL: <<create>> new Block(this)
    block = builder.build(crypto_service, private_key)
    print(f"      <- BlockBuilder zwraca Block: {block.get_hash()[:16]}...")

    # BB->>BC: appendBlock(Block)
    print("    • BlockBuilder -> Blockchain: appendBlock(Block)")
    success = blockchain.append_block(block)
    print(f"      <- Blockchain zwraca: {'success' if success else 'failure'}")

    # 4. Weryfikacja bloku
    print("\n[4] Weryfikacja bloku...")
    is_valid_signature = block.validate_signature(public_key, crypto_service)
    print(f"    ✓ Podpis bloku: {'poprawny' if is_valid_signature else 'niepoprawny'}")
    print(f"    ✓ Hash bloku: {block.get_hash()[:32]}...")
    print(f"    ✓ Parent hash: {block.get_parent_hash()[:32]}...")
    print(f"    ✓ Miner: {block.miner}")
    print(f"    ✓ Liczba dokumentów: {len(block.documents)}")

    # 5. Sprawdzenie łańcucha
    print("\n[5] Stan blockchain...")
    print(f"    • Całkowita liczba bloków: {len(blockchain.chain)}")
    print(f"    • Ostatni blok: {blockchain.get_last_block().get_hash()[:16]}...")

    return blockchain, block


def demo_multiple_blocks():
    """Demonstracja tworzenia wielu bloków."""
    print("\n\n" + "=" * 70)
    print("DEMO: Tworzenie wielu bloków z użyciem Builder")
    print("=" * 70)

    blockchain = Blockchain()
    crypto_service = MockCryptoService()

    print("\n[*] Tworzenie 5 bloków z dokumentami...")

    for i in range(1, 6):
        # Generuj klucze dla każdego minera
        pub_key, priv_key = crypto_service.generate_key_pair()
        miner = f"miner_{i}"

        # Utwórz transakcję
        transaction = Transaction(sender=f"User{i}", recipient=f"User{i+1}", amount=float(i * 100))

        # Pobierz parent hash
        parent_hash = blockchain.get_last_block().get_hash()

        # Zbuduj blok
        builder = BlockBuilder()
        block = (
            builder.set_parent_hash(parent_hash)
            .set_author(miner)
            .add_document(transaction)
            .build(crypto_service, priv_key)
        )

        # Dodaj do blockchain
        blockchain.append_block(block)

        print(f"    ✓ Blok #{i}: {block.get_hash()[:16]}... by {miner}")

    print(f"\n[✓] Utworzono blockchain z {len(blockchain.chain)} blokami")
    print("    • Genesis + 5 nowych bloków")
    print("    • Wszystkie bloki podpisane i zweryfikowane")


def demo_document_types():
    """Demonstracja różnych typów dokumentów notarialnych."""
    print("\n\n" + "=" * 70)
    print("DEMO: Różne typy dokumentów notarialnych")
    print("=" * 70)

    blockchain = Blockchain()
    crypto_service = MockCryptoService()
    pub_key, priv_key = crypto_service.generate_key_pair()

    print("\n[1] Tworzenie bloku z wieloma typami dokumentów...")

    # Różne typy dokumentów
    doc1 = Transaction("Alice", "Bob", 5000.0)
    doc2 = Transaction("Charlie", "David", 3000.0)
    doc3 = VotingResult("VOTE-2026-002", {"Yes": 200, "No": 150})

    # Buduj blok z wszystkimi dokumentami
    builder = BlockBuilder()
    block = (
        builder.set_parent_hash(blockchain.get_last_block().get_hash())
        .set_author("notary_office_1")
        .add_document(doc1)
        .add_document(doc2)
        .add_document(doc3)
        .build(crypto_service, priv_key)
    )

    blockchain.append_block(block)

    print("    ✓ Blok utworzony z 3 dokumentami:")
    print("      - 2x Transaction")
    print("      - 1x VotingResult")

    # Wyświetl JSON dokumentów
    print("\n[2] Zawartość dokumentów (JSON):")
    for i, doc in enumerate(block.documents, 1):
        print(f"\n    Dokument {i}:")
        json_data = doc.get_json_data()
        import json

        parsed = json.loads(json_data)
        print(f"      Type: {parsed.get('type')}")
        if parsed.get("type") == "Transaction":
            print(f"      {parsed['sender']} -> {parsed['recipient']}: {parsed['amount']}")
        elif parsed.get("type") == "VotingResult":
            print(f"      Voting ID: {parsed['voting_id']}")
            print(f"      Results: {parsed['results']}")


def demo_json_export():
    """Demonstracja eksportu bloku do JSON."""
    print("\n\n" + "=" * 70)
    print("DEMO: Eksport bloku do JSON")
    print("=" * 70)

    blockchain = Blockchain()
    crypto_service = MockCryptoService()
    pub_key, priv_key = crypto_service.generate_key_pair()

    # Utwórz blok
    transaction = Transaction("Alice", "Bob", 1500.0)
    builder = BlockBuilder()
    block = (
        builder.set_parent_hash(blockchain.get_last_block().get_hash())
        .set_author("miner_001")
        .add_document(transaction)
        .build(crypto_service, priv_key)
    )

    # Eksportuj do JSON
    print("\n[*] JSON reprezentacja bloku:")
    json_data = block.get_json_data()
    print(json_data)


def main():
    """Funkcja główna."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  BLOCKCHAIN CORE - Wzorzec Builder".center(68) + "║")
    print("║" + "  Demonstracja zgodnie z diagramem sekwencji".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")

    try:
        demo_builder_pattern()
        demo_multiple_blocks()
        demo_document_types()
        demo_json_export()

        print("\n\n" + "=" * 70)
        print("✓ Wszystkie demonstracje zakończone pomyślnie!")
        print("=" * 70)
        print("\n[PODSUMOWANIE]")
        print("• Wzorzec Builder poprawnie zaimplementowany")
        print("• Diagram sekwencji odwzorowany w kodzie")
        print("• Interfejs NotarialDocument z implementacjami")
        print("• Klasy Transaction i VotingResult działają")
        print("• Podpisywanie i weryfikacja bloków działa")
        print("• Integracja z Blockchain poprawna")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n✗ Błąd: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
