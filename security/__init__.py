__all__ = [
	"X509Certificate",
	"KeyStore",
	"TrustStore",
	"CertificateValidator",
	"IdentityManager",
	"BlockSigner",
	"SecurityModuleAdapter",
]


def __getattr__(name: str):
	if name not in __all__:
		raise AttributeError(name)
	from .adapter import SecurityModuleAdapter
	from .block_signer import BlockSigner
	from .certificate import X509Certificate
	from .identity_manager import IdentityManager
	from .key_store import KeyStore
	from .trust_store import TrustStore
	from .validator import CertificateValidator

	exports = {
		"X509Certificate": X509Certificate,
		"KeyStore": KeyStore,
		"TrustStore": TrustStore,
		"CertificateValidator": CertificateValidator,
		"IdentityManager": IdentityManager,
		"BlockSigner": BlockSigner,
		"SecurityModuleAdapter": SecurityModuleAdapter,
	}
	globals().update(exports)
	return exports[name]
