from typing import List, Dict, Optional
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from .certificate import X509Certificate

class TrustStore:
    """
    Przechowuje zaufane certyfikaty Root CA oraz zweryfikowane certyfikaty innych węzłów.
    """
    
    def __init__(self):
        self._trusted_roots: List[X509Certificate] = []
        self._peer_certs: Dict[str, X509Certificate] = {} # Map Subject Name -> Cert

    def load_trusted_root(self, path: str):
        """Ładuje certyfikat Root CA z pliku."""
        with open(path, "rb") as f:
            cert = x509.load_pem_x509_certificate(f.read())
            self._trusted_roots.append(cert)

    def add_peer_certificate(self, cert: X509Certificate):
        """Dodaje certyfikat innego węzła (peera)."""
        # Używamy sformatowanego Name jako klucza
        subject_name = cert.subject.rfc4514_string()
        self._peer_certs[subject_name] = cert

    def get_root_ca(self, issuer_name: x509.Name) -> Optional[X509Certificate]:
        """Szuka zaufanego Root CA, który pasuje do podanego wystawcy (Issuer)."""
        for root in self._trusted_roots:
            if root.subject == issuer_name:
                return root
        return None
