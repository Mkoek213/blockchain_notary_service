from typing import Any, Dict, Tuple
from cryptography import x509
from blockchain_core.crypto_service import ICryptoService
from .identity_manager import IdentityManager

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
        UWAGA: W tej implementacji parametr `public_key` musi być stringiem
        zawierającym certyfikat X.509 w formacie PEM.
        """
        import json
        data_bytes = json.dumps(block_data, sort_keys=True).encode('utf-8')
        signature_bytes = bytes.fromhex(signature)
        
        # Parsujemy certyfikat z PEM stringa
        try:
            cert = x509.load_pem_x509_certificate(public_key.encode('utf-8'))
            return self.identity_manager.verify_peer_signature(data_bytes, signature_bytes, cert)
        except Exception as e:
            print(f"Błąd parsowania certyfikatu w adapterze: {e}")
            return False

    def generate_key_pair(self) -> Tuple[str, str]:
        """
        Metoda zdeprecjonowana w modelu PKI. 
        Zwraca certyfikat węzła (jako klucz publiczny) i pusty string prywatny.
        """
        cert = self.identity_manager.get_self_certificate()
        if not cert:
            raise RuntimeError("Identity not initialized")
            
        cert_pem = cert.public_bytes(
            encoding=x509.encoding.PEM
        ).decode('utf-8')
        
        return (cert_pem, "private-key-managed-internally")
