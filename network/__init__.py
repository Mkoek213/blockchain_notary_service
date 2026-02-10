__all__ = [
    "NetworkManager",
    "PeerManager",
    "PeerConnection",
    "IPeerConnection",
    "IConnectionListener",
    "NetworkMessage",
    "BlockSynchronizer",
    "DiscoveryService",
    "block_from_dict",
    "document_from_dict",
]


def __getattr__(name: str):
    if name not in __all__:
        raise AttributeError(name)
    from .block_adapter import block_from_dict, document_from_dict
    from .discovery import DiscoveryService
    from .message import NetworkMessage
    from .network_manager import NetworkManager
    from .peer_connection import IConnectionListener, IPeerConnection, PeerConnection
    from .peer_manager import PeerManager
    from .synchronizer import BlockSynchronizer

    exports = {
        "NetworkManager": NetworkManager,
        "PeerManager": PeerManager,
        "PeerConnection": PeerConnection,
        "IPeerConnection": IPeerConnection,
        "IConnectionListener": IConnectionListener,
        "NetworkMessage": NetworkMessage,
        "BlockSynchronizer": BlockSynchronizer,
        "DiscoveryService": DiscoveryService,
        "block_from_dict": block_from_dict,
        "document_from_dict": document_from_dict,
    }
    globals().update(exports)
    return exports[name]
