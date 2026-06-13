from __future__ import annotations

import json
import secrets
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from app.config import get_settings
from app.legal_pages import end_user_license_agreement, privacy_policy
from app.nrs import NrsClient
from app.quickbooks import QuickBooksClient
from app.rev360 import Rev360Client
from app.storage import Storage
from app.sync import InvoiceSyncService


settings = get_settings()
storage = Storage(settings.database_path)
quickbooks = QuickBooksClient(settings, storage)
nrs = NrsClient(settings)
rev360 = Rev360Client(settings)
sync_service = InvoiceSyncService(settings, storage, quickbooks, nrs)
oauth_states: set[str] = set()


class Handler(BaseHTTPRequestHandler):
    server_version = "NRSQuickBooksAPI/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.send_json({"ok": True})
            return
        if parsed.path == "/legal/privacy":
            self.send_html(privacy_policy())
            return
        if parsed.path == "/legal/eula":
            self.send_html(end_user_license_agreement())
            return
        if parsed.path == "/rev360/config":
            self.rev360_config()
            return
        if parsed.path.startswith("/rev360/e-invoices/"):
            self.rev360_status(parsed.path)
            return
        if parsed.path == "/auth/quickbooks/start":
            self.start_quickbooks_auth()
            return
        if parsed.path == "/auth/quickbooks/callback":
            self.quickbooks_callback(parsed.query)
            return
        self.send_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/webhooks/nrs/invoice":
            self.nrs_invoice_webhook()
            return
        if parsed.path == "/sync/invoices":
            self.sync_invoices()
            return
        if parsed.path == "/rev360/e-invoices/preview":
            self.rev360_preview()
            return
        if parsed.path == "/rev360/e-invoices":
            self.rev360_submit(parsed.query)
            return
        self.send_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)

    def start_quickbooks_auth(self) -> None:
        state = secrets.token_urlsafe(24)
        oauth_states.add(state)
        self.send_response(HTTPStatus.FOUND)
        self.send_header("Location", quickbooks.authorization_url(state))
        self.end_headers()

    def quickbooks_callback(self, query: str) -> None:
        values = parse_qs(query)
        state = values.get("state", [""])[0]
        code = values.get("code", [""])[0]
        realm_id = values.get("realmId", [""])[0]

        if state not in oauth_states:
            self.send_json({"error": "invalid_oauth_state"}, HTTPStatus.BAD_REQUEST)
            return
        oauth_states.discard(state)
        if not code or not realm_id:
            self.send_json({"error": "missing_code_or_realm_id"}, HTTPStatus.BAD_REQUEST)
            return

        try:
            quickbooks.exchange_code(code, realm_id)
            self.send_html("<h1>QuickBooks connected</h1><p>You can close this tab and start syncing invoices.</p>")
        except Exception as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_GATEWAY)

    def nrs_invoice_webhook(self) -> None:
        if settings.nrs_webhook_secret:
            supplied = self.headers.get("X-NRS-Webhook-Secret", "")
            if supplied != settings.nrs_webhook_secret:
                self.send_json({"error": "invalid_webhook_secret"}, HTTPStatus.UNAUTHORIZED)
                return

        invoice = self.read_json_body()
        if invoice is None:
            return
        try:
            result = sync_service.sync_one(invoice)
            self.send_json(result)
        except Exception as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_GATEWAY)

    def sync_invoices(self) -> None:
        body = self.read_json_body(default={})
        if body is None:
            return
        try:
            result = sync_service.sync_from_nrs(body.get("updated_since"))
            self.send_json(result)
        except Exception as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_GATEWAY)

    def rev360_config(self) -> None:
        self.send_json(
            {
                "base_url": settings.rev360_base_url,
                "report_base_url": settings.rev360_report_base_url,
                "erp_name": settings.rev360_erp_name,
                "entity_id": settings.rev360_entity_id,
                "business_id": settings.rev360_business_id,
                "submit_path": settings.rev360_submit_path,
                "status_path": settings.rev360_status_path,
                "api_key_configured": bool(settings.rev360_api_key),
                "client_secret_configured": bool(settings.rev360_client_secret),
            }
        )

    def rev360_preview(self) -> None:
        invoice = self.read_json_body()
        if invoice is None:
            return
        try:
            self.send_json(rev360.build_einvoice_payload(invoice))
        except Exception as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def rev360_submit(self, query: str = "") -> None:
        invoice = self.read_json_body()
        if invoice is None:
            return
        query_values = parse_qs(query)
        dry_run_value = query_values.get("dry_run", [""])[0]
        dry_run = dry_run_value.lower() in {"1", "true", "yes"} or self.headers.get("X-Dry-Run", "").lower() in {"1", "true", "yes"}
        try:
            result = rev360.submit_einvoice(invoice, dry_run=dry_run)
            payload = result.get("payload", {})
            storage.record_rev360_submission(
                payload.get("irn", ""),
                payload.get("invoice_id", ""),
                result["status"],
                payload,
                response_payload=result.get("response"),
            )
            self.send_json(result)
        except Exception as exc:
            try:
                payload = rev360.build_einvoice_payload(invoice)
                storage.record_rev360_submission(payload.get("irn", ""), payload.get("invoice_id", ""), "failed", payload, error_message=str(exc))
            except Exception:
                pass
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_GATEWAY)

    def rev360_status(self, path: str) -> None:
        irn = path.rsplit("/", 1)[-1]
        if not irn:
            self.send_json({"error": "missing_irn"}, HTTPStatus.BAD_REQUEST)
            return
        try:
            self.send_json(rev360.get_einvoice_status(irn))
        except Exception as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_GATEWAY)

    def read_json_body(self, default: dict | None = None) -> dict | None:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0 and default is not None:
            return default
        raw = self.rfile.read(length).decode("utf-8")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            self.send_json({"error": "invalid_json"}, HTTPStatus.BAD_REQUEST)
            return None

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        raw = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def send_html(self, html: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        raw = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


def main() -> None:
    server = ThreadingHTTPServer((settings.app_host, settings.app_port), Handler)
    print(f"Listening on http://{settings.app_host}:{settings.app_port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
