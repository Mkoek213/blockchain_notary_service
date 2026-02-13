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
from security.identity_manager import IdentityManager
from security import SecurityModuleAdapter

# Stałe ścieżki
PKI_DIR = "pki"
CA_KEY_PATH = os.path.join(PKI_DIR, "ca", "root_ca.key")
CA_CERT_PATH = os.path.join(PKI_DIR, "ca", "root_ca.crt")
NODE_CONFIG_DIR = os.path.join(PKI_DIR, "node_config")
NODE_KEY_PATH = os.path.join(NODE_CONFIG_DIR, "node.key")
NODE_CERT_PATH = os.path.join(NODE_CONFIG_DIR, "node.crt")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Notary Service UI")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--storage", action="store_true", help="Enable file-based storage")
    parser.add_argument("--data-dir", type=str, default="data")
    parser.add_argument("--enable-network", action="store_true")
    parser.add_argument("--p2p-port", type=int, default=8545)
    parser.add_argument("--target-peers", type=int, default=3)
    parser.add_argument("--max-peers", type=int, default=3)
    parser.add_argument("--seed-peers", type=str, default="")
    parser.add_argument("--node-name", type=str, default="ui-node")
    # Przywrócone argumenty dla kompatybilności z Dockerem
    parser.add_argument("--key-path", type=str, default=None)
    parser.add_argument("--cert-path", type=str, default=None)
    parser.add_argument("--ca-path", type=str, default=None)
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

    def _check_auth(self) -> bool:
        """Sprawdza czy węzeł jest zalogowany (czy ma tożsamość)."""
        im = self.server.identity_manager # type: ignore
        return im.get_self_certificate() is not None

    def _get_state_payload(self) -> Dict[str, Any]:
        # Jeśli nie zalogowany, zwróć pusty stan
        if not self._check_auth():
            return {"state": {}, "chain": {}, "auth": False}

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
        
        # Pobierz nazwę zalogowanego węzła
        cert = self.server.identity_manager.get_self_certificate() # type: ignore
        node_dn = cert.subject.rfc4514_string() if cert else "Unknown"
        
        return {"state": state, "chain": chain_stats, "auth": True, "node_dn": node_dn}

    def _get_block_payload(self, height: Optional[int]) -> Dict[str, Any]:
        if not self._check_auth():
             return {"error": "Unauthorized"}
             
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
        
        # Sprawdzamy status auth dla API
        if self.path == "/api/auth-status":
            is_logged = self._check_auth()
            # Sprawdź czy jest zarejestrowany (czy pliki istnieją)
            is_registered = os.path.exists(NODE_KEY_PATH)
            self._json({"logged_in": is_logged, "registered": is_registered})
            return

        if self.path == "/api/state":
            self._json(self._get_state_payload())
            return
        if self.path == "/api/chain":
            self._json(self._get_state_payload().get("chain", {}))
            return
        if self.path == "/api/peers":
            if not self._check_auth():
                self._json({"error": "Unauthorized"}, status=401)
                return
            network = getattr(self.server.service, "network_manager", None)  # type: ignore[attr-defined]
            peer_list = []
            if network is not None and network.peer_manager is not None:
                for peer in list(network.peer_manager.peers.values()):
                    endpoint = getattr(peer, "remote_endpoint", None)
                    peer_list.append(
                        {
                            "peer_id": getattr(peer, "peer_id", ""),
                            "endpoint": list(endpoint) if endpoint else None,
                            "height": getattr(peer, "remote_height", 0),
                            "latest_hash": getattr(peer, "remote_hash", ""),
                        }
                    )
            self._json({"peers": peer_list})
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

        im = self.server.identity_manager # type: ignore
        service = self.server.service  # type: ignore[attr-defined]

        # --- ENDPOINTY AUTH ---

        if self.path == "/api/register":
            name = data.get("name")
            password = data.get("password")
            if not name or not password:
                self._json({"error": "Missing name or password"}, status=400)
                return
            
            try:
                # Upewnij się że CA istnieje
                if not os.path.exists(CA_KEY_PATH):
                     # Fallback dla demo - uruchom pki_setup jeśli nie ma
                     import pki_setup
                     pki_setup.setup_pki()

                im.register_new_node(
                    name=name,
                    organization="NotaryUI",
                    password=password,
                    output_dir=NODE_CONFIG_DIR,
                    ca_key_path=CA_KEY_PATH,
                    ca_cert_path=CA_CERT_PATH
                )
                self._json({"ok": True})
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, status=500)
            return

        if self.path == "/api/login":
            password = data.get("password")
            if not password:
                self._json({"error": "Missing password"}, status=400)
                return
            
            try:
                im.load_identity(
                    key_path=NODE_KEY_PATH,
                    cert_path=NODE_CERT_PATH,
                    trusted_root_path=CA_CERT_PATH,
                    password=password
                )
                
                # Zaktualizuj serwis o nową tożsamość
                adapter = SecurityModuleAdapter(im)
                service.blockchain.crypto_service = adapter
                service.notary_validator.crypto_service = adapter
                
                # Jeśli sieć nie działa, a powinna - uruchom ją teraz
                # (zakładamy, że args.enable_network było przekazane do serwera lub jest domyślne true dla UI)
                # W tym miejscu nie mamy dostępu do `args` z main, więc możemy użyć flagi w service?
                # Service ma network_manager, ale może być None jeśli enable_network było False
                if service.network_manager:
                    # Sprawdź czy już działa? Metoda start jest idempotentna w NetworkManager?
                    # W NetworkManager nie ma flagi `running`, ale `start()` uruchamia sockety.
                    # Bezpieczniej założyć, że jeśli nie było tożsamości, to nie wystartował.
                    # Ale musimy znać port.
                    # Dla uproszczenia: w UI hardkodujemy port 8545 lub bierzemy z service.
                    service.start_network(8545) # Domyślny port
                
                self._json({"ok": True})
            except Exception as e:
                print(f"Login error: {e}")
                self._json({"ok": False, "error": "Invalid password or key file"}, status=401)
            return

        # --- ENDPOINTY BIZNESOWE (WYMAGAJĄ ZALOGOWANIA) ---
        
        if not self._check_auth():
            self._json({"error": "Unauthorized. Please login first."}, status=401)
            return

        # Pobierz DN autora
        author_dn = im.get_self_certificate().subject.rfc4514_string()

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
            # Używamy ignorowanego klucza, bo adapter ma go w sobie
            block = service.build_block(author=author_dn, documents=[doc], sign=True, private_key="ignored")
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
            block = service.build_block(author=author_dn, documents=[doc], sign=True, private_key="ignored")
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
            block = service.build_block(author=author_dn, documents=[doc], sign=True, private_key="ignored")
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
            block = service.build_block(author=author_dn, documents=[doc], sign=True, private_key="ignored")
            added = service.add_block(block)
            if added:
                service.broadcast_block(block)
            self._json({"ok": True, "valid": True, "added": added, "document_id": document_id})
            return

        if self.path == "/api/resolution":
            required = ["resolution_id", "company_id", "resolution_type", "votes_for", "votes_against"]
            if not all(k in data for k in required):
                self._json({"error": "Missing fields"}, status=400)
                return
            document_id = data.get("document_id") or str(uuid.uuid4())
            doc_data = {
                "type": "Resolution",
                "document_id": document_id,
                "resolution_id": data["resolution_id"],
                "company_id": data["company_id"],
                "resolution_type": data["resolution_type"],
                "votes_for": int(data["votes_for"]),
                "votes_against": int(data["votes_against"]),
                "votes_abstain": int(data.get("votes_abstain", 0)),
                "voters": data.get("voters", []),
                "signatures": [],
            }
            is_valid = service.validate_document(doc_data)
            if not is_valid:
                self._json({"ok": False, "valid": False, "error": "Validation failed"})
                return
            doc = service.create_document(doc_data)
            block = service.build_block(author=author_dn, documents=[doc], sign=True, private_key="ignored")
            added = service.add_block(block)
            if added:
                service.broadcast_block(block)
            self._json({"ok": True, "valid": True, "added": added, "document_id": document_id})
            return

        if self.path == "/api/resolution":
            required = ["resolution_id", "company_id", "resolution_type", "votes_for", "votes_against"]
            if not all(k in data for k in required):
                self._json({"error": "Missing fields"}, status=400)
                return
            document_id = data.get("document_id") or str(uuid.uuid4())
            doc_data = {
                "type": "Resolution",
                "document_id": document_id,
                "resolution_id": data["resolution_id"],
                "company_id": data["company_id"],
                "resolution_type": data["resolution_type"],
                "votes_for": int(data["votes_for"]),
                "votes_against": int(data["votes_against"]),
                "votes_abstain": int(data.get("votes_abstain", 0)),
                "voters": data.get("voters", []),
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
    
    # Inicjalizacja IdentityManager (ale bez ładowania tożsamości jeszcze)
    identity_manager = IdentityManager()
    
    auto_login_success = False
    
    # Próba załadowania jeśli podano argumenty (np. z CLI Dockera)
    if args.key_path and args.cert_path:
        try:
            # W trybie Dockerowym hasło może być puste (jeśli klucze niezaszyfrowane) lub z ENV
            password = os.getenv("NODE_PASSWORD", None)
            
            # Jeśli ca_path nie jest podany, spróbuj domyślny
            ca_path = args.ca_path or CA_CERT_PATH
            
            identity_manager.load_identity(
                key_path=args.key_path,
                cert_path=args.cert_path,
                trusted_root_path=ca_path,
                password=password
            )
            print("Zalogowano automatycznie używając argumentów CLI.")
            auto_login_success = True
        except Exception as e:
            print(f"Ostrzeżenie: Nie udało się zalogować automatycznie: {e}")

    seed_peers = []
    if args.seed_peers:
        for item in args.seed_peers.split(","):
            entry = item.strip()
            if not entry or ":" not in entry:
                continue
            host, port_text = entry.rsplit(":", 1)
            try:
                port_value = int(port_text)
            except ValueError:
                continue
            seed_peers.append((host, port_value))

    service = NotaryService(
        use_storage=args.storage,
        data_dir=args.data_dir,
        enable_network=args.enable_network,
        identity_manager=identity_manager,
        target_peers=args.target_peers,
        # Jeśli zalogowano automatycznie, wstrzyknij adapter
        crypto_service=SecurityModuleAdapter(identity_manager) if auto_login_success else None,
        max_peers=args.max_peers,
        seed_peers=seed_peers,
    )
    
    if args.enable_network:
        # Uruchom sieć TYLKO jeśli zalogowano
        if auto_login_success:
            service.start_network(args.p2p_port)
        else:
            print("Sieć nie została uruchomiona (oczekiwanie na logowanie użytkownika).")
        
    ui_html = load_html()

    server = ThreadingHTTPServer((args.host, args.port), NotaryUIHandler)
    server.service = service  # type: ignore[attr-defined]
    server.identity_manager = identity_manager # type: ignore[attr-defined]
    server.ui_html = ui_html  # type: ignore[attr-defined]

    print(f"UI running on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
