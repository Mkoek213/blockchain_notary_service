import datetime
import os
from typing import Tuple

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

PKI_DIR = "pki"
CA_DIR = os.path.join(PKI_DIR, "ca")
NODE_DIR = os.path.join(PKI_DIR, "node")

def generate_key_pair():
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

def save_key(key, path):
    with open(path, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

def save_cert(cert, path):
    with open(path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

def load_ca(ca_dir: str) -> Tuple[serialization.PrivateFormat, x509.Certificate]:
    key_path = os.path.join(ca_dir, "root_ca.key")
    cert_path = os.path.join(ca_dir, "root_ca.crt")
    with open(key_path, "rb") as key_file:
        ca_key = serialization.load_pem_private_key(key_file.read(), password=None)
    with open(cert_path, "rb") as cert_file:
        ca_cert = x509.load_pem_x509_certificate(cert_file.read())
    return ca_key, ca_cert


def ensure_ca(ca_dir: str = CA_DIR) -> Tuple[serialization.PrivateFormat, x509.Certificate]:
    os.makedirs(ca_dir, exist_ok=True)
    key_path = os.path.join(ca_dir, "root_ca.key")
    cert_path = os.path.join(ca_dir, "root_ca.crt")
    if os.path.exists(key_path) and os.path.exists(cert_path):
        return load_ca(ca_dir)

    ca_key = generate_key_pair()
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"PL"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"NotaryChamber"),
            x509.NameAttribute(NameOID.COMMON_NAME, u"NotaryRootCA"),
        ]
    )
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(ca_key, hashes.SHA256())
    )

    save_key(ca_key, key_path)
    save_cert(ca_cert, cert_path)
    return ca_key, ca_cert


def generate_node_identity(
    common_name: str,
    node_dir: str = NODE_DIR,
    ca_dir: str = CA_DIR,
) -> Tuple[str, str]:
    os.makedirs(node_dir, exist_ok=True)
    ca_key, ca_cert = ensure_ca(ca_dir)
    node_key = generate_key_pair()
    node_subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"PL"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"KancelariaKowalski"),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
    )

    csr = x509.CertificateSigningRequestBuilder().subject_name(node_subject).sign(
        node_key, hashes.SHA256()
    )

    node_cert = (
        x509.CertificateBuilder()
        .subject_name(csr.subject)
        .issuer_name(ca_cert.subject)
        .public_key(csr.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(ca_key, hashes.SHA256())
    )

    key_path = os.path.join(node_dir, f"{common_name}.key")
    cert_path = os.path.join(node_dir, f"{common_name}.crt")
    save_key(node_key, key_path)
    save_cert(node_cert, cert_path)
    return key_path, cert_path


def setup_pki():
    os.makedirs(CA_DIR, exist_ok=True)
    os.makedirs(NODE_DIR, exist_ok=True)
    ensure_ca(CA_DIR)
    key_path = os.path.join(NODE_DIR, "node.key")
    cert_path = os.path.join(NODE_DIR, "node.crt")
    if not os.path.exists(key_path) or not os.path.exists(cert_path):
        generate_node_identity("Node-01", NODE_DIR, CA_DIR)

    print("PKI Setup Complete.")
    print(f"Root CA Path: {os.path.join(CA_DIR, 'root_ca.crt')}")
    print(f"Node Key Path: {os.path.join(NODE_DIR, 'node.key')}")
    print(f"Node Cert Path: {os.path.join(NODE_DIR, 'node.crt')}")

if __name__ == "__main__":
    setup_pki()
