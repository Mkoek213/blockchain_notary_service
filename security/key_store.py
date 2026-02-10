from typing import Optional
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from .certificate import X509Certificate

class KeyStore:
    """
    Komponent odpowiedzialny za bezpieczne przechowywanie klucza prywatnego
    oraz certyfikatu własnego węzła.
    """
    
    def __init__(self):
        self._private_key: Optional[rsa.RSAPrivateKey] = None
        self._self_certificate: Optional[X509Certificate] = None

    def load_identity(self, private_key_pem: bytes, certificate: X509Certificate):
        """Ładuje tożsamość (klucz prywatny i certyfikat) do KeyStore."""
        self._private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None
        )
        self._self_certificate = certificate

    def get_self_certificate(self) -> Optional[X509Certificate]:
        return self._self_certificate

    def sign(self, data: bytes) -> bytes:
        """Podpisuje dane używając przechowywanego klucza prywatnego."""
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

    # Metoda pomocnicza do generowania kluczy na potrzeby demo
    @staticmethod
    def generate_new_identity(subject_dn: str) -> 'KeyStore':
        ks = KeyStore()
        # Generowanie pary kluczy RSA
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        ks._private_key = private_key
        
        # Eksport klucza publicznego do stringa dla uproszczonego certyfikatu
        public_key_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        # Tworzenie "certyfikatu"
        ks._self_certificate = X509Certificate(
            subject_dn=subject_dn,
            issuer_dn="CN=NotaryCA", # Mock issuer
            public_key=public_key_pem
        )
        return ks
