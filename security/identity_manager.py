import os
from typing import Optional
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from .certificate import X509Certificate
from .key_store import KeyStore
from .trust_store import TrustStore
from .validator import CertificateValidator
from .pki_utils import generate_key_pair, create_csr, sign_csr, save_private_key, save_cert

class IdentityManager:
    """
    Fasada (Facade) dla modułu bezpieczeństwa.
    Obsługuje teraz również proces rejestracji (generowanie tożsamości).
    """
    
    def __init__(self):
        self.key_store = KeyStore()
        self.trust_store = TrustStore()
        self.validator = CertificateValidator(self.trust_store)

    def load_identity(self, key_path: str, cert_path: str, trusted_root_path: str, password: str = None):
        """
        Logowanie: Inicjalizuje węzeł ładując tożsamość z plików.
        """
        # 1. Załaduj nasze klucze (wsparcie dla szyfrowanych kluczy)
        self.key_store.load_from_files(key_path, cert_path, password)
        
        # 2. Załaduj zaufane Root CA
        if os.path.exists(trusted_root_path):
            self.trust_store.load_trusted_root(trusted_root_path)
        else:
            print(f"Ostrzeżenie: Nie znaleziono Root CA pod ścieżką {trusted_root_path}")

    def register_new_node(self, name: str, organization: str, password: str, 
                          output_dir: str, ca_key_path: str, ca_cert_path: str):
        """
        Rejestracja: Generuje nową tożsamość i zapisuje na dysk.
        Symuluje proces w Izbie (używa klucza CA do podpisu).
        """
        # 1. Załaduj klucze CA (Izby) do podpisu
        with open(ca_key_path, "rb") as f:
            ca_key = serialization.load_pem_private_key(f.read(), password=None)
        with open(ca_cert_path, "rb") as f:
            ca_cert = x509.load_pem_x509_certificate(f.read())

        # 2. Generuj klucz prywatny Węzła
        node_key = generate_key_pair()
        
        # 3. Stwórz CSR
        csr = create_csr(node_key, common_name=name, organization=organization)
        
        # 4. Podpisz certyfikat (Symulacja Izby)
        node_cert = sign_csr(csr, ca_cert, ca_key)
        
        # 5. Zapisz pliki
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        key_path = os.path.join(output_dir, "node.key")
        cert_path = os.path.join(output_dir, "node.crt")
        
        save_private_key(node_key, key_path, password)
        save_cert(node_cert, cert_path)
        
        print(f"Zarejestrowano pomyślnie! Klucze w: {output_dir}")
        return key_path, cert_path

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
