from typing import Any, Dict, Tuple
from blockchain_core.crypto_service import ICryptoService
from .identity_manager import IdentityManager
from .certificate import X509Certificate

class SecurityModuleAdapter(ICryptoService):
    """
    Adapter pozwalający używać nowego modułu security (IdentityManager)
    poprzez stary interfejs ICryptoService (używany przez Block).
    """
    
    def __init__(self, identity_manager: IdentityManager):
        self.identity_manager = identity_manager

    def sign_block(self, block_data: Dict[str, Any], private_key: str) -> str:
        """
        Podpisuje blok.
        Parametr private_key jest ignorowany, bo IdentityManager zarządza kluczem wewnętrznie.
        """
        import json
        # Deterministyczna serializacja
        data_bytes = json.dumps(block_data, sort_keys=True).encode('utf-8')
        signature = self.identity_manager.sign_data(data_bytes)
        return signature.hex()

    def verify_signature(self, block_data: Dict[str, Any], signature: str, public_key: str) -> bool:
        """
        Weryfikuje podpis.
        Parametr public_key tutaj traktujemy jako PEM string klucza publicznego,
        musimy go zapakować w X509Certificate (mock) żeby przekazać do walidatora.
        """
        import json
        data_bytes = json.dumps(block_data, sort_keys=True).encode('utf-8')
        signature_bytes = bytes.fromhex(signature)
        
        # Tworzymy tymczasowy certyfikat z kluczem publicznym
        # (W prawdziwym systemie public_key byłby całym certyfikatem lub jego ID)
        cert = X509Certificate(
            subject_dn="Unknown",
            issuer_dn="Unknown",
            public_key=public_key
        )
        
        return self.identity_manager.verify_peer_signature(data_bytes, signature_bytes, cert)

    def generate_key_pair(self) -> Tuple[str, str]:
        """
        Generuje nową tożsamość i zwraca klucze (mock/wrapper).
        """
        # Ta metoda w oryginalnym interfejsie zwracała (pub, priv).
        # W nowym modelu to IdentityManager zarządza kluczami.
        # Możemy wygenerować tymczasowy KeyStore.
        from .key_store import KeyStore
        ks = KeyStore.generate_new_identity("CN=Generated")
        # Wyciągamy PEM
        cert = ks.get_self_certificate()
        # Klucz prywatny nie jest łatwo dostępny jako string w naszym KeyStore (bezpieczeństwo),
        # ale na potrzeby adaptera możemy to ominąć lub rzucić wyjątek.
        # W KeyStore private_key jest obiektem rsa.
        
        from cryptography.hazmat.primitives import serialization
        priv_pem = ks._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        return (cert.public_key, priv_pem)
