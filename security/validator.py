from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature
from .certificate import X509Certificate
from .trust_store import TrustStore

class CertificateValidator:
    """
    Klasa odpowiedzialna za walidację certyfikatów i weryfikację podpisów.
    """

    def __init__(self, trust_store: TrustStore):
        self.trust_store = trust_store

    def validate_certificate(self, cert: X509Certificate) -> bool:
        """
        Sprawdza czy certyfikat został podpisany przez zaufane Root CA.
        """
        # Znajdź Root CA który wydał ten certyfikat
        root_ca = self.trust_store.get_root_ca(cert.issuer)
        
        if not root_ca:
            print(f"Nieznany wystawca certyfikatu: {cert.issuer.rfc4514_string()}")
            return False
            
        # Weryfikacja kryptograficzna podpisu na certyfikacie
        public_key = root_ca.public_key()
        try:
            public_key.verify(
                cert.signature,
                cert.tbs_certificate_bytes,
                padding.PKCS1v15(), # Certyfikaty CA zazwyczaj są podpisane PKCS1v15
                cert.signature_hash_algorithm
            )
            return True
        except InvalidSignature:
            print("Certyfikat ma niepoprawny podpis (fałszywy lub uszkodzony)")
            return False
        except Exception as e:
            print(f"Błąd walidacji certyfikatu: {e}")
            return False

    def verify_signature(self, data: bytes, signature: bytes, cert: X509Certificate) -> bool:
        """
        Weryfikuje podpis cyfrowy danych używając klucza publicznego z certyfikatu.
        """
        try:
            public_key = cert.public_key()
            public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except InvalidSignature:
            return False
        except Exception as e:
            print(f"Błąd weryfikacji podpisu danych: {e}")
            return False
