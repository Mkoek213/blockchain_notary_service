import os
import datetime
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

def generate_key_pair():
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

def save_private_key(key, path, password: str):
    """Zapisuje klucz prywatny zaszyfrowany hasłem."""
    encryption = serialization.BestAvailableEncryption(password.encode()) if password else serialization.NoEncryption()
    
    with open(path, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption
        ))

def save_cert(cert, path):
    """Zapisuje certyfikat publiczny."""
    with open(path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

def create_csr(private_key, common_name: str, organization: str, country: str = "PL"):
    """Tworzy żądanie podpisu certyfikatu (CSR)."""
    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, country),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    
    return x509.CertificateSigningRequestBuilder().subject_name(
        subject
    ).sign(private_key, hashes.SHA256())

def sign_csr(csr, ca_cert, ca_key, days=365):
    """Podpisuje CSR kluczem CA (Symulacja Izby)."""
    return x509.CertificateBuilder().subject_name(
        csr.subject
    ).issuer_name(
        ca_cert.subject
    ).public_key(
        csr.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=days)
    ).add_extension(
        x509.BasicConstraints(ca=False, path_length=None), critical=True,
    ).sign(ca_key, hashes.SHA256())
