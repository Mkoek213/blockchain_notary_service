from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
from .certificate import X509Certificate
from .trust_store import TrustStore

class CertificateValidator:
    """
    Klasa odpowiedzialna za walidację certyfikatów i weryfikację podpisów.
    """

    def __init__(self, trust_store: TrustStore):
        self.trust_store = trust_store

    def validate(self, cert: X509Certificate) -> bool:
        """
        Waliduje certyfikat (sprawdza czy jest wystawiony przez zaufane CA).
        W pełnej implementacji sprawdzałby łańcuch certyfikatów, daty ważności, CRL itp.
        """
        # Mockowa walidacja: sprawdzamy czy Issuer DN certyfikatu
        # odpowiada któremuś z zaufanych Root CA.
        for root in self.trust_store._trusted_roots:
            if root.get_subject_dn() == cert.get_issuer_dn():
                return True
        return False

    def verify_signature(self, data: bytes, signature: bytes, cert: X509Certificate) -> bool:
        """
        Weryfikuje podpis cyfrowy danych używając klucza publicznego z certyfikatu.
        """
        try:
            # Ładujemy klucz publiczny z certyfikatu (który jest w formacie PEM string)
            public_key = serialization.load_pem_public_key(
                cert.public_key.encode('utf-8')
            )
            
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
        except (InvalidSignature, ValueError):
            return False
        except Exception as e:
            print(f"Błąd weryfikacji podpisu: {e}")
            return False
