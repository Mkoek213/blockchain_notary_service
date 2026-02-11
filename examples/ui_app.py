import argparse
import json
import logging
import os
import sys
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from notary_service import NotaryService
from pki_setup import CA_DIR, NODE_DIR, generate_node_identity, setup_pki
from security.identity_manager import IdentityManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Notary Service UI")
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--storage", action="store_true", help="Enable file-based storage")
    parser.add_argument("--data-dir", type=str, default="data")
    parser.add_argument("--enable-network", action="store_true")
    parser.add_argument("--p2p-port", type=int, default=8545)
    parser.add_argument("--discovery-port", type=int, default=9999)
    parser.add_argument("--node-name", type=str, default="ui-node")
    parser.add_argument("--key-path", type=str, default="")
    parser.add_argument("--cert-path", type=str, default="")
    parser.add_argument("--ca-path", type=str, default="")
    return parser


def load_html() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "ui_app.html")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class NotaryUIHandler(BaseHTTPRequestHandler):
    server_version = "NotaryUI/1.0"

    def _json(self, payload: Dict[str, Any], status: int = 200) -> None:
        data = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _text(self, payload: str, status: int = 200, content_type: str = "text/html") -> None:
        data = payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _parse_json(self) -> Optional[Dict[str, Any]]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return None
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
            if isinstance(data, dict):
                return data
            return None
        except Exception:
            return None

    def _get_state_payload(self) -> Dict[str, Any]:
        ws = self.server.service.world_state  # type: ignore[attr-defined]
        if hasattr(ws, "export_state"):
            state = ws.export_state()
        else:
            shares = []
            for (account_id, company_id), count in ws._shares.items():
                shares.append(
                    {
                        "account_id": account_id,
                        "company_id": company_id,
                        "shares": count,
                    }
                )
            state = {
                "balances": dict(ws._balances),
                "shares": shares,
                "companies": dict(ws._companies),
                "processed_documents": sorted(ws._processed_documents),
            }
        entities = set()
        for key in state.get("balances", {}).keys():
            entities.add(key)
        for entry in state.get("shares", []):
            account_id = entry.get("account_id")
            if account_id:
                entities.add(account_id)
        for key in state.get("companies", {}).keys():
            entities.add(key)
        state["entities"] = sorted(entities)
        blockchain = self.server.service.blockchain  # type: ignore[attr-defined]
        chain_stats = {
            "height": blockchain.get_height(),
            "latest_hash": blockchain.get_latest_block_hash(),
        }
        return {"state": state, "chain": chain_stats}

    def _get_block_payload(self, height: Optional[int]) -> Dict[str, Any]:
        blockchain = self.server.service.blockchain  # type: ignore[attr-defined]
        max_height = blockchain.get_height() - 1
        if max_height < 0:
            return {"height": None, "max_height": -1, "block": None}
        if height is None:
            height = max_height
        if height < 0 or height > max_height:
            return {"height": height, "max_height": max_height, "block": None}
        block = blockchain.chain[height]
        payload = block.to_dict() if hasattr(block, "to_dict") else block
        return {"height": height, "max_height": max_height, "block": payload}

    def do_GET(self) -> None:
        if self.path == "/":
            self._text(self.server.ui_html)  # type: ignore[attr-defined]
            return
        if self.path == "/api/state":
            self._json(self._get_state_payload())
            return
        if self.path == "/api/chain":
            self._json(self._get_state_payload()["chain"])
            return
        if self.path.startswith("/api/block"):
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            height_value = query.get("height", [None])[0]
            height = int(height_value) if height_value is not None else None
            self._json(self._get_block_payload(height))
            return
        self._text("Not Found", status=404, content_type="text/plain")

    def do_POST(self) -> None:
        data = self._parse_json()
        if data is None:
            self._json({"error": "Invalid JSON"}, status=400)
            return

        service = self.server.service  # type: ignore[attr-defined]

        if self.path == "/api/company":
            company_id = data.get("company_id")
            name = data.get("name", "")
            if not company_id:
                self._json({"error": "company_id is required"}, status=400)
                return
            doc_data = {
                "type": "CompanyRegistration",
                "document_id": data.get("document_id") or str(uuid.uuid4()),
                "company_id": company_id,
                "name": name,
                "signatures": [],
            }
            if not service.validate_document(doc_data):
                self._json({"ok": False, "valid": False, "error": "Validation failed"})
                return
            doc = service.create_document(doc_data)
            block = service.build_block(author="ui-notary", documents=[doc])
            added = service.add_block(block)
            if added:
                service.broadcast_block(block)
            self._json({"ok": True, "added": added, "document_id": doc_data["document_id"]})
            return

        if self.path == "/api/shares":
            account_id = data.get("account_id")
            company_id = data.get("company_id")
            shares = data.get("shares")
            if not account_id or not company_id or shares is None:
                self._json({"error": "account_id, company_id, shares are required"}, status=400)
                return
            doc_data = {
                "type": "SharesAllocation",
                "document_id": data.get("document_id") or str(uuid.uuid4()),
                "account_id": account_id,
                "company_id": company_id,
                "shares": int(shares),
                "signatures": [],
            }
            if not service.validate_document(doc_data):
                self._json({"ok": False, "valid": False, "error": "Validation failed"})
                return
            doc = service.create_document(doc_data)
            block = service.build_block(author="ui-notary", documents=[doc])
            added = service.add_block(block)
            if added:
                service.broadcast_block(block)
            self._json({"ok": True, "added": added, "document_id": doc_data["document_id"]})
            return

        if self.path == "/api/balance":
            account_id = data.get("account_id")
            balance = data.get("balance")
            if not account_id or balance is None:
                self._json({"error": "account_id, balance are required"}, status=400)
                return
            doc_data = {
                "type": "BalanceUpdate",
                "document_id": data.get("document_id") or str(uuid.uuid4()),
                "account_id": account_id,
                "balance": float(balance),
                "signatures": [],
            }
            if not service.validate_document(doc_data):
                self._json({"ok": False, "valid": False, "error": "Validation failed"})
                return
            doc = service.create_document(doc_data)
            block = service.build_block(author="ui-notary", documents=[doc])
            added = service.add_block(block)
            if added:
                service.broadcast_block(block)
            self._json({"ok": True, "added": added, "document_id": doc_data["document_id"]})
            return

        if self.path == "/api/transfer":
            required = ["seller", "buyer", "company_id", "shares_count", "price_per_share"]
            if not all(k in data for k in required):
                self._json({"error": "Missing fields"}, status=400)
                return
            document_id = data.get("document_id") or str(uuid.uuid4())
            doc_data = {
                "type": "SharesTransfer",
                "document_id": document_id,
                "seller": data["seller"],
                "buyer": data["buyer"],
                "company_id": data["company_id"],
                "shares_count": int(data["shares_count"]),
                "price_per_share": float(data["price_per_share"]),
                "signatures": [],
            }
            is_valid = service.validate_document(doc_data)
            if not is_valid:
                self._json({"ok": False, "valid": False, "error": "Validation failed"})
                return
            doc = service.create_document(doc_data)
            block = service.build_block(author="ui-notary", documents=[doc])
            added = service.add_block(block)
            if added:
                service.broadcast_block(block)
            self._json({"ok": True, "valid": True, "added": added, "document_id": document_id})
            return

        self._json({"error": "Not Found"}, status=404)


def main() -> None:
    args = build_parser().parse_args()
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    identity_manager: Optional[IdentityManager] = None
    if args.enable_network:
        if not args.key_path or not args.cert_path or not args.ca_path:
            setup_pki()
            node_key_path, node_cert_path = generate_node_identity(args.node_name, NODE_DIR, CA_DIR)
            args.key_path = args.key_path or node_key_path
            args.cert_path = args.cert_path or node_cert_path
            args.ca_path = args.ca_path or os.path.join(CA_DIR, "root_ca.crt")

        identity_manager = IdentityManager()
        identity_manager.load_identity(
            key_path=args.key_path,
            cert_path=args.cert_path,
            trusted_root_path=args.ca_path,
        )

    service = NotaryService(
        use_storage=args.storage,
        data_dir=args.data_dir,
        enable_network=args.enable_network,
        identity_manager=identity_manager,
        discovery_port=args.discovery_port,
    )
    if args.enable_network:
        service.start_network(args.p2p_port)
    ui_html = load_html()

    server = ThreadingHTTPServer((args.host, args.port), NotaryUIHandler)
    server.service = service  # type: ignore[attr-defined]
    server.ui_html = ui_html  # type: ignore[attr-defined]

    print(f"UI running on http://{args.host}:{args.port}")
    if args.enable_network:
        print(f"P2P listening on {args.p2p_port}, discovery UDP {args.discovery_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
