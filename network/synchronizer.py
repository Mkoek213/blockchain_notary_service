from typing import Any, Dict, List

from blockchain_core.interfaces import IBlockchainInterface

from .block_adapter import block_from_dict
from .message import NetworkMessage
from .peer_manager import PeerManager
from .types import MessageType


class BlockSynchronizer:
    def __init__(self, chain: IBlockchainInterface, peers: PeerManager) -> None:
        self.chain = chain
        self.peers = peers
        self.is_syncing = False

    def sync_blockchain(self) -> bool:
        if self.is_syncing:
            return False
        peer = self.peers.get_best_peer()
        if peer is None:
            return False
        local_height = self.chain.get_height()
        if peer.remote_height <= local_height:
            return True
        self.is_syncing = True
        self._request_missing_blocks(peer)
        return True

    def _request_missing_blocks(self, peer: Any) -> None:
        payload = {"from_height": self.chain.get_height()}
        peer.send(NetworkMessage(type=MessageType.GET_BLOCKS, payload=payload))

    def handle_block_response(self, payload: Dict[str, Any]) -> None:
        blocks_data: List[Dict[str, Any]] = payload.get("blocks", [])
        for block_data in blocks_data:
            block = block_from_dict(block_data)
            if block is None:
                continue
            self.chain.validate_and_add_block(block)
        self.is_syncing = False
