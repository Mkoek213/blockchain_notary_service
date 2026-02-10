import json
import pytest
import os
import shutil
from security import IdentityManager, BlockSigner
from blockchain_core.block_builder import BlockBuilder
from blockchain_core.notarial_document import Transaction
from pki_setup import setup_pki, PKI_DIR

@pytest.fixture(scope="session")
def pki_environment():
    """Fixture, który generuje klucze przed testami i sprząta po nich."""
    # 1. Setup
    print("\n[Fixture] Setting up PKI...")
    setup_pki()
    
    yield
    
    # 2. Teardown (opcjonalnie - na razie zostawmy pliki do inspekcji)
    # if os.path.exists(PKI_DIR):
    #     shutil.rmtree(PKI_DIR)

@pytest.fixture
def identity_manager(pki_environment):
    """Fixture inicjalizujący IdentityManager z prawdziwymi kluczami."""
    im = IdentityManager()
    
    im.load_identity(
        key_path=os.path.join(PKI_DIR, "node", "node.key"),
        cert_path=os.path.join(PKI_DIR, "node", "node.crt"),
        trusted_root_path=os.path.join(PKI_DIR, "ca", "root_ca.crt")
    )
    return im

def test_full_security_flow(identity_manager):
    signer = BlockSigner(identity_manager)
    
    # 1. Tworzenie bloku
    tx = Transaction("Alice", "Bob", 500.0)
    builder = BlockBuilder()
    builder.set_parent_hash("abc" * 20)
    builder.set_author("CN=Node-01")
    builder.add_document(tx)
    block = builder.build()
    
    # 2. Podpisywanie
    signed_block = signer.sign_block(block)
    
    print(f"Signed Hash: {signed_block.hash}")
    print(f"Signature Len: {len(signed_block.extra_data)}")
    
    # 3. Weryfikacja
    # Symulujemy, że inny węzeł otrzymuje blok.
    # Musi pobrać certyfikat autora (zazwyczaj jest przesyłany z blokiem lub znany w sieci)
    author_cert = identity_manager.get_self_certificate()
    
    # KROK A: Walidacja certyfikatu autora (czy jest od zaufanego Root CA?)
    is_cert_valid = identity_manager.validate_peer(author_cert)
    assert is_cert_valid, "Certyfikat autora powinien być zaufany (podpisany przez Root CA)"
    
    # KROK B: Weryfikacja podpisu pod blokiem
    signable_data = signed_block._get_signable_data()
    data_bytes = json.dumps(signable_data, sort_keys=True).encode('utf-8')
    signature_bytes = bytes.fromhex(signed_block.extra_data)
    
    is_sig_valid = identity_manager.verify_peer_signature(data_bytes, signature_bytes, author_cert)
    assert is_sig_valid, "Podpis bloku powinien być poprawny"