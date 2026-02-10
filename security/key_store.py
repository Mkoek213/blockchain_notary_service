from typing import Optional
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from .certificate import X509Certificate

class KeyStore:
    """
    Komponent odpowiedzialny za bezpieczne przechowywanie klucza prywatnego
    oraz certyfikatu własnego węzła.
    """
    
    def __init__(self):
        self._private_key: Optional[rsa.RSAPrivateKey] = None
        self._self_certificate: Optional[X509Certificate] = None

    def load_from_files(self, key_path: str, cert_path: str, password: str = None):
        """Ładuje klucz prywatny i certyfikat z plików PEM."""
        with open(key_path, "rb") as f:
            self._private_key = serialization.load_pem_private_key(
                f.read(),
                password=password.encode() if password else None
            )
            
        with open(cert_path, "rb") as f:
            self._self_certificate = x509.load_pem_x509_certificate(f.read())

    def get_self_certificate(self) -> Optional[X509Certificate]:
        return self._self_certificate

    def sign(self, data: bytes) -> bytes:
        """Podpisuje dane używając przechowywanego klucza prywatnego (SHA256 + RSA PSS)."""
        if not self._private_key:
            raise RuntimeError("KeyStore not initialized with private key")

        signature = self._private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature
