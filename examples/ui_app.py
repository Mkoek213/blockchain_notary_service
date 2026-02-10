import argparse
import json
import os
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional

from notary_service import NotaryService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Notary Service UI")
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--storage", action="store_true", help="Enable file-based storage")
    parser.add_argument("--data-dir", type=str, default="data")
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
        blockchain = self.server.service.blockchain  # type: ignore[attr-defined]
        chain_stats = {
            "height": blockchain.get_height(),
            "latest_hash": blockchain.get_latest_block_hash(),
        }
        return {"state": state, "chain": chain_stats}

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
            service.world_state.register_company(company_id, name)
            self._json({"ok": True})
            return

        if self.path == "/api/shares":
            account_id = data.get("account_id")
            company_id = data.get("company_id")
            shares = data.get("shares")
            if not account_id or not company_id or shares is None:
                self._json({"error": "account_id, company_id, shares are required"}, status=400)
                return
            service.world_state.set_shares(account_id, company_id, int(shares))
            self._json({"ok": True})
            return

        if self.path == "/api/balance":
            account_id = data.get("account_id")
            balance = data.get("balance")
            if not account_id or balance is None:
                self._json({"error": "account_id, balance are required"}, status=400)
                return
            service.world_state.set_balance(account_id, float(balance))
            self._json({"ok": True})
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
            self._json({"ok": True, "valid": True, "added": added, "document_id": document_id})
            return

        self._json({"error": "Not Found"}, status=404)


def main() -> None:
    args = build_parser().parse_args()
    service = NotaryService(use_storage=args.storage, data_dir=args.data_dir)
    ui_html = load_html()

    server = ThreadingHTTPServer((args.host, args.port), NotaryUIHandler)
    server.service = service  # type: ignore[attr-defined]
    server.ui_html = ui_html  # type: ignore[attr-defined]

    print(f"UI running on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
