from typing import Optional
from .certificate import X509Certificate
from .key_store import KeyStore
from .trust_store import TrustStore
from .validator import CertificateValidator

class IdentityManager:
    """
    Fasada (Facade) dla modułu bezpieczeństwa.
    Ukrywa złożoność zarządzania kluczami, certyfikatami i walidacją.
    """
    
    def __init__(self):
        self.key_store = KeyStore()
        self.trust_store = TrustStore()
        self.validator = CertificateValidator(self.trust_store)

    def load_identity(self, key_path: str, cert_path: str, trusted_root_path: str):
        """
        Inicjalizuje węzeł ładując tożsamość z plików.
        """
        # 1. Załaduj nasze klucze
        self.key_store.load_from_files(key_path, cert_path)
        
        # 2. Załaduj zaufane Root CA
        self.trust_store.load_trusted_root(trusted_root_path)

    def get_self_certificate(self) -> Optional[X509Certificate]:
        return self.key_store.get_self_certificate()

    def sign_data(self, data: bytes) -> bytes:
        """Podpisuje dane własnym kluczem prywatnym."""
        return self.key_store.sign(data)

    def validate_peer(self, cert: X509Certificate) -> bool:
        """Waliduje certyfikat innego węzła (czy wydany przez nasze CA)."""
        return self.validator.validate_certificate(cert)
    
    def verify_peer_signature(self, data: bytes, signature: bytes, cert: X509Certificate) -> bool:
        """Weryfikuje podpis innego węzła."""
        return self.validator.verify_signature(data, signature, cert)
    
    def add_peer_certificate(self, cert: X509Certificate):
        """Dodaje zaufany (już zweryfikowany) certyfikat peera do cache."""
        self.trust_store.add_peer_certificate(cert)
