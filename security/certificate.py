from dataclasses import dataclass
from typing import Optional

@dataclass
class X509Certificate:
    """
    Uproszczona reprezentacja certyfikatu X.509 na potrzeby projektu.
    W rzeczywistości byłaby to klasa z biblioteki kryptograficznej (np. cryptography.x509).
    """
    subject_dn: str
    issuer_dn: str
    public_key: str  # W uproszczeniu trzymamy klucz jako string (PEM lub hex)
    serial_number: int = 1
    
    def get_subject_dn(self) -> str:
        return self.subject_dn
        
    def get_issuer_dn(self) -> str:
        return self.issuer_dn
    
    def get_public_key(self) -> str:
        return self.public_key

    def __str__(self):
        return f"Certificate(Subject: {self.subject_dn}, Issuer: {self.issuer_dn})"
