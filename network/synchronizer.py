import json
from typing import Any, Dict, List, Optional

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
        self._expect_full_sync = False
        self._full_sync_hash: Optional[str] = None

    def sync_blockchain(self) -> bool:
        if self.is_syncing:
            return False
        local_height = self.chain.get_height()
        higher_peers, best_peer = self._get_higher_peers()
        if higher_peers > 2 and best_peer is not None:
            local_hash = self.chain.get_latest_block_hash()
            if best_peer.remote_hash and best_peer.remote_hash != local_hash:
                self.is_syncing = True
                self._expect_full_sync = True
                self._full_sync_hash = best_peer.remote_hash
                self._request_missing_blocks(best_peer, from_height=0)
                return True
            if best_peer.remote_height > local_height:
                self.is_syncing = True
                self._expect_full_sync = False
                self._full_sync_hash = None
                self._request_missing_blocks(best_peer)
                return True
        majority_hash, majority_count = self._get_majority_hash()
        local_hash = self.chain.get_latest_block_hash()
        total_peers = self.peers.get_peer_count()
        if majority_hash and majority_hash != local_hash and majority_count > total_peers / 2:
            peer = self._get_peer_by_hash(majority_hash)
            if peer is None:
                return False
            self.is_syncing = True
            self._expect_full_sync = True
            self._full_sync_hash = majority_hash
            self._request_missing_blocks(peer, from_height=0)
            return True
        peer = self.peers.get_best_peer()
        if peer is None:
            return False
        if peer.remote_height <= local_height:
            return True
        self.is_syncing = True
        self._expect_full_sync = False
        self._full_sync_hash = None
        self._request_missing_blocks(peer)
        return True

    def _request_missing_blocks(self, peer: Any, from_height: Optional[int] = None) -> None:
        start_height = self.chain.get_height() if from_height is None else from_height
        payload = {"from_height": start_height}
        peer.send(NetworkMessage(type=MessageType.GET_BLOCKS, payload=payload))

    def handle_block_response(self, payload: Dict[str, Any]) -> None:
        blocks_data: List[Dict[str, Any]] = payload.get("blocks", [])
        if self._expect_full_sync:
            old_blocks = self.chain.get_blocks_from(0)
            blocks: List[Any] = []
            for block_data in blocks_data:
                block = block_from_dict(block_data)
                if block is None:
                    self._reset_sync_state()
                    return
                blocks.append(block)
            if hasattr(self.chain, "replace_chain"):
                if self.chain.replace_chain(blocks):
                    self._requeue_orphaned_documents(old_blocks, blocks)
                    self._reset_sync_state()
                    return
            self._reset_sync_state()
            return
        for block_data in blocks_data:
            block = block_from_dict(block_data)
            if block is None:
                self._reset_sync_state()
                return
            if not self.chain.validate_and_add_block(block):
                self._reset_sync_state()
                return
        self._reset_sync_state()

    def _reset_sync_state(self) -> None:
        self.is_syncing = False
        self._expect_full_sync = False
        self._full_sync_hash = None

    def _get_majority_hash(self) -> tuple[Optional[str], int]:
        peers = self.peers.get_peer_snapshots()
        if not peers:
            return None, 0
        counts: Dict[str, int] = {}
        for _, _, remote_hash in peers:
            if not remote_hash:
                continue
            counts[remote_hash] = counts.get(remote_hash, 0) + 1
        if not counts:
            return None, 0
        majority_hash = max(counts.items(), key=lambda item: item[1])[0]
        return majority_hash, counts[majority_hash]

    def _get_peer_by_hash(self, target_hash: str) -> Optional[Any]:
        best_peer = None
        best_height = -1
        for _, peer_height, peer_hash in self.peers.get_peer_snapshots():
            if peer_hash == target_hash and peer_height > best_height:
                best_height = peer_height
        if best_height < 0:
            return None
        for peer in self.peers.peers.values():
            if peer.remote_hash == target_hash and peer.remote_height == best_height:
                return peer
        return None

    def _get_higher_peers(self) -> tuple[int, Optional[Any]]:
        local_height = self.chain.get_height()
        count = 0
        best_peer = None
        best_height = -1
        for peer in self.peers.peers.values():
            if peer.remote_height > local_height:
                count += 1
                if peer.remote_height > best_height:
                    best_height = peer.remote_height
                    best_peer = peer
        return count, best_peer

    def _requeue_orphaned_documents(self, old_blocks: List[Any], new_blocks: List[Any]) -> None:
        new_doc_keys = self._collect_document_keys(new_blocks)
        orphan_docs: List[Dict[str, Any]] = []
        for block in old_blocks:
            for doc in getattr(block, "documents", []):
                data = self._doc_to_dict(doc)
                if data is None:
                    continue
                key = self._doc_key(data)
                if key in new_doc_keys:
                    continue
                orphan_docs.append(data)
        for doc in orphan_docs:
            self.chain.handle_transactions(doc)

    def _collect_document_keys(self, blocks: List[Any]) -> set[str]:
        keys: set[str] = set()
        for block in blocks:
            for doc in getattr(block, "documents", []):
                data = self._doc_to_dict(doc)
                if data is None:
                    continue
                keys.add(self._doc_key(data))
        return keys

    def _doc_to_dict(self, doc: Any) -> Optional[Dict[str, Any]]:
        if hasattr(doc, "to_dict"):
            data = doc.to_dict()
            return data if isinstance(data, dict) else None
        if hasattr(doc, "get_json_data"):
            try:
                data = json.loads(doc.get_json_data())
                return data if isinstance(data, dict) else None
            except Exception:
                return None
        if isinstance(doc, dict):
            return doc
        return None

    def _doc_key(self, data: Dict[str, Any]) -> str:
        validator = getattr(self.chain, "notary_validator", None)
        if validator is not None and hasattr(validator, "get_document_hash"):
            try:
                return str(validator.get_document_hash(data))
            except Exception:
                pass
        return json.dumps(data, sort_keys=True, ensure_ascii=True)
