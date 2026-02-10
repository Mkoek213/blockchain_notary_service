from typing import List, Dict, Optional
from .certificate import X509Certificate

class TrustStore:
    """
    Przechowuje zaufane certyfikaty (CA) oraz zweryfikowane certyfikaty innych węzłów.
    """
    
    def __init__(self):
        self._trusted_roots: List[X509Certificate] = []
        self._peer_certs: Dict[str, X509Certificate] = {} # Map subjectDN -> Cert

    def add_trusted_root(self, cert: X509Certificate):
        """Dodaje certyfikat CA do listy zaufanych."""
        self._trusted_roots.append(cert)

    def add_peer_certificate(self, cert: X509Certificate):
        """Dodaje certyfikat innego węzła (peera)."""
        self._peer_certs[cert.get_subject_dn()] = cert

    def get_cached_certificate(self, subject_dn: str) -> Optional[X509Certificate]:
        """Pobiera certyfikat peera po Subject DN."""
        return self._peer_certs.get(subject_dn)

    def is_root_trusted(self, cert: X509Certificate) -> bool:
        """Sprawdza czy dany certyfikat znajduje się na liście zaufanych rootów."""
        # W uproszczeniu porównujemy po DN
        for root in self._trusted_roots:
            if root.get_subject_dn() == cert.get_subject_dn():
                return True
        return False
