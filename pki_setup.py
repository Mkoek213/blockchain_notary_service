import os
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.x509.oid import NameOID
import datetime

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

def setup_pki():
    if not os.path.exists(PKI_DIR):
        os.makedirs(CA_DIR)
        os.makedirs(NODE_DIR)
        print(f"Created directories: {PKI_DIR}")

    # 1. Generowanie Root CA (Izba Notarialna)
    print("Generating Root CA...")
    ca_key = generate_key_pair()
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"PL"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"NotaryChamber"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"NotaryRootCA"),
    ])
    
    ca_cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        ca_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        # Ważny 10 lat
        datetime.datetime.utcnow() + datetime.timedelta(days=3650)
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=None), critical=True,
    ).sign(ca_key, hashes.SHA256())

    save_key(ca_key, os.path.join(CA_DIR, "root_ca.key"))
    save_cert(ca_cert, os.path.join(CA_DIR, "root_ca.crt"))

    # 2. Generowanie Tożsamości Węzła (Notariusz)
    print("Generating Node Identity...")
    node_key = generate_key_pair()
    node_subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"PL"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"KancelariaKowalski"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"Node-01"),
    ])

    # Tworzenie CSR (Certificate Signing Request) - normalnie to wysyłamy do CA
    csr = x509.CertificateSigningRequestBuilder().subject_name(
        node_subject
    ).sign(node_key, hashes.SHA256())

    # 3. Podpisanie certyfikatu węzła przez CA
    print("Signing Node Certificate by CA...")
    node_cert = x509.CertificateBuilder().subject_name(
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
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.BasicConstraints(ca=False, path_length=None), critical=True,
    ).sign(ca_key, hashes.SHA256())

    save_key(node_key, os.path.join(NODE_DIR, "node.key"))
    save_cert(node_cert, os.path.join(NODE_DIR, "node.crt"))

    print("PKI Setup Complete.")
    print(f"Root CA Path: {os.path.join(CA_DIR, 'root_ca.crt')}")
    print(f"Node Key Path: {os.path.join(NODE_DIR, 'node.key')}")
    print(f"Node Cert Path: {os.path.join(NODE_DIR, 'node.crt')}")

if __name__ == "__main__":
    setup_pki()
