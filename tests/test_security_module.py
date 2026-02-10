import json
import pytest
from security import IdentityManager, BlockSigner
from blockchain_core.block_builder import BlockBuilder
from blockchain_core.notarial_document import Transaction

@pytest.fixture
def security_components():
    """Fixture initializing IdentityManager and BlockSigner for tests."""
    identity_manager = IdentityManager()
    # Generujemy nową tożsamość "w locie"
    identity_manager.initialize_for_demo(subject_dn="CN=TestNode,O=NotaryService,C=PL")
    signer = BlockSigner(identity_manager)
    return identity_manager, signer

def test_sign_and_verify_block(security_components):
    identity_manager, signer = security_components
    
    # 1. Stwórz blok używając BlockBuilder
    tx = Transaction("Alice", "Bob", 100.0)
    
    builder = BlockBuilder()
    builder.set_parent_hash("0" * 64)
    builder.set_author("CN=TestNode")
    builder.add_document(tx)
    
    # Budujemy blok bez podpisywania przez stary mechanizm (crypto_service=None)
    block = builder.build()
    
    print(f"Block hash before signing: {block.hash}")
    print(f"Extra data before signing: {block.extra_data}")
    
    # 2. Podpisz blok używając nowego BlockSigner
    signed_block = signer.sign_block(block)
    
    print(f"Block hash after signing: {signed_block.hash}")
    print(f"Signature (extra_data): {signed_block.extra_data}")
    
    assert len(signed_block.extra_data) > 0, "Block should have extra_data (signature)"
    assert signed_block.hash != "0"*64, "Block hash should be calculated"

    # 3. Weryfikacja podpisu
    # Do weryfikacji potrzebujemy certyfikatu autora.
    # W tym teście autor to my sami.
    cert = identity_manager.get_self_certificate()
    
    # Pobieramy dane, które były podpisane (te same co w BlockSigner)
    signable_data = signed_block._get_signable_data()
    data_bytes = json.dumps(signable_data, sort_keys=True).encode('utf-8')
    signature_bytes = bytes.fromhex(signed_block.extra_data)
    
    # Weryfikujemy używając IdentityManager (walidacja peera)
    # Tutaj weryfikujemy podpis "peera" (którym jesteśmy my sami w tym teście)
    is_valid = identity_manager.verify_peer_signature(data_bytes, signature_bytes, cert)
    
    assert is_valid, "Signature verification failed"
