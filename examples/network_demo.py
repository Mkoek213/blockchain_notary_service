import argparse
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from blockchain_core.interfaces import IBlockchainInterface
from network.network_manager import NetworkManager
from security.identity_manager import IdentityManager
from pki_setup import CA_DIR, NODE_DIR, generate_node_identity, setup_pki


@dataclass
class DemoBlock:
    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.data)


@dataclass
class DemoBlockchain(IBlockchainInterface):
    height: int = 1
    latest_hash: str = "genesis"
    blocks: List[DemoBlock] = field(default_factory=list)

    def get_height(self) -> int:
        return self.height

    def get_last_block(self) -> Optional[DemoBlock]:
        return self.blocks[-1] if self.blocks else None

    def get_blocks_range(self, start: int, end: int) -> List[DemoBlock]:
        if start < 0 or end < start:
            return []
        return self.blocks[start : end + 1]

    def validate_and_add_block(self, block: Any) -> bool:
        data = block.to_dict() if hasattr(block, "to_dict") else dict(block)
        self.blocks.append(DemoBlock(data))
        self.height += 1
        self.latest_hash = data.get("hash", self.latest_hash)
        print(f"[block] {json.dumps(data, sort_keys=True)}")
        return True

    def get_latest_block_hash(self) -> str:
        return self.latest_hash

    def has_block(self, hash: str) -> bool:
        return any(block.data.get("hash") == hash for block in self.blocks)

    def handle_transactions(self, tx_data: dict) -> None:
        print(f"[tx] {json.dumps(tx_data, sort_keys=True)}")

    def get_blocks_from(self, height: int) -> List[DemoBlock]:
        if height < 0:
            return []
        return self.blocks[height:]


def parse_peers(values: Sequence[str]) -> List[Tuple[str, int]]:
    peers: List[Tuple[str, int]] = []
    for value in values:
        if ":" not in value:
            continue
        host, port = value.rsplit(":", 1)
        try:
            peers.append((host, int(port)))
        except ValueError:
            continue
    return peers


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8545)
    parser.add_argument("--discovery-port", type=int, default=9999)
    parser.add_argument("--name", type=str, default="peer")
    parser.add_argument("--peer", action="append", default=[])
    parser.add_argument("--message", type=str, default="")
    parser.add_argument("--interval", type=float, default=0.0)
    parser.add_argument("--no-stdin", action="store_true")
    parser.add_argument("--key-path", type=str, default="")
    parser.add_argument("--cert-path", type=str, default="")
    parser.add_argument("--ca-path", type=str, default="")
    return parser


def build_message(name: str, text: str) -> Dict[str, Any]:
    return {"type": "chat", "from": name, "text": text, "ts": time.time()}


def run_broadcast_loop(manager: NetworkManager, name: str, text: str, interval: float) -> None:
    while True:
        manager.broadcast_transaction(build_message(name, text))
        if interval <= 0:
            return
        time.sleep(interval)


def run_stdin_loop(manager: NetworkManager, name: str) -> None:
    for line in sys.stdin:
        text = line.strip()
        if not text:
            continue
        manager.broadcast_transaction(build_message(name, text))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    if not args.key_path or not args.cert_path or not args.ca_path:
        setup_pki()
        node_key_path, node_cert_path = generate_node_identity(args.name, NODE_DIR, CA_DIR)
        args.key_path = args.key_path or node_key_path
        args.cert_path = args.cert_path or node_cert_path
        args.ca_path = args.ca_path or os.path.join(CA_DIR, "root_ca.crt")

    identity_manager = IdentityManager()
    identity_manager.load_identity(
        key_path=args.key_path,
        cert_path=args.cert_path,
        trusted_root_path=args.ca_path,
    )
    chain = DemoBlockchain()
    manager = NetworkManager(
        chain=chain,
        identity_manager=identity_manager,
        listen_port=args.port,
        discovery_port=args.discovery_port,
    )
    manager.start(args.port)
    print(f"[node] {args.name} listening on {args.port}")
    print(f"[node] discovery on udp {args.discovery_port}")

    peers = parse_peers(args.peer)
    for host, port in peers:
        manager.peer_manager.add_candidate(host, port)
        print(f"[node] connecting to {host}:{port}")
    manager.peer_manager.maintain_connections()

    if args.message:
        run_broadcast_loop(manager, args.name, args.message, args.interval)

    if not args.no_stdin:
        try:
            run_stdin_loop(manager, args.name)
        except KeyboardInterrupt:
            return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
