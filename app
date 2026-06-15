from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    app_host: str
    app_port: int
    app_base_url: str
    database_path: str
    quickbooks_environment: str
    quickbooks_client_id: str
    quickbooks_client_secret: str
    quickbooks_redirect_uri: str
    quickbooks_minor_version: str
    nrs_api_base_url: str
    nrs_api_token: str
    nrs_invoice_path: str
    nrs_webhook_secret: str
    rev360_base_url: str
    rev360_report_base_url: str
    rev360_erp_name: str
    rev360_entity_id: str
    rev360_business_id: str
    rev360_api_key: str
    rev360_client_secret: str
    rev360_irn_template: str
    rev360_submit_path: str
    rev360_status_path: str
    default_qb_item_name: str
    default_qb_income_account_name: str

    @property
    def quickbooks_api_base_url(self) -> str:
        return "https://sandbox-quickbooks.api.intuit.com" if self.quickbooks_environment == "sandbox" else "https://quickbooks.api.intuit.com"


def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        app_host=os.getenv("APP_HOST", "127.0.0.1"),
        app_port=int(os.getenv("APP_PORT", "8080")),
        app_base_url=os.getenv("APP_BASE_URL", "http://localhost:8080"),
        database_path=os.getenv("APP_DATABASE_PATH", "work/integration.sqlite3"),
        quickbooks_environment=os.getenv("QUICKBOOKS_ENVIRONMENT", "sandbox"),
        quickbooks_client_id=os.getenv("QUICKBOOKS_CLIENT_ID", ""),
        quickbooks_client_secret=os.getenv("QUICKBOOKS_CLIENT_SECRET", ""),
        quickbooks_redirect_uri=os.getenv("QUICKBOOKS_REDIRECT_URI", "http://localhost:8080/auth/quickbooks/callback"),
        quickbooks_minor_version=os.getenv("QUICKBOOKS_MINOR_VERSION", "75"),
        nrs_api_base_url=os.getenv("NRS_API_BASE_URL", ""),
        nrs_api_token=os.getenv("NRS_API_TOKEN", ""),
        nrs_invoice_path=os.getenv("NRS_INVOICE_PATH", "/invoices"),
        nrs_webhook_secret=os.getenv("NRS_WEBHOOK_SECRET", ""),
        rev360_base_url=os.getenv("REV360_BASE_URL", "https://eivc-k6z6d.ondigitalocean.app"),
        rev360_report_base_url=os.getenv("REV360_REPORT_BASE_URL", "https://api.firsmbs.com"),
        rev360_erp_name=os.getenv("REV360_ERP_NAME", "QuickBooks"),
        rev360_entity_id=os.getenv("REV360_ENTITY_ID", ""),
        rev360_business_id=os.getenv("REV360_BUSINESS_ID", ""),
        rev360_api_key=os.getenv("REV360_API_KEY", ""),
        rev360_client_secret=os.getenv("REV360_CLIENT_SECRET", ""),
        rev360_irn_template=os.getenv("REV360_IRN_TEMPLATE", "{{invoice_id}}-1A57E861-{{YYYYMMDD}}"),
        rev360_submit_path=os.getenv("REV360_SUBMIT_PATH", "/api/v1/e-invoices"),
        rev360_status_path=os.getenv("REV360_STATUS_PATH", "/api/v1/e-invoices/{irn}"),
        default_qb_item_name=os.getenv("DEFAULT_QB_ITEM_NAME", "NRS Sales"),
        default_qb_income_account_name=os.getenv("DEFAULT_QB_INCOME_ACCOUNT_NAME", "Sales"),
    )

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class HttpError(RuntimeError):
    def __init__(self, status: int, body: str) -> None:
        super().__init__(f"HTTP {status}: {body}")
        self.status = status
        self.body = body


def request_json(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    data: dict[str, Any] | None = None,
    form: dict[str, str] | None = None,
) -> dict[str, Any] | list[Any]:
    body: bytes | None = None
    request_headers = dict(headers or {})

    if data is not None:
        body = json.dumps(data).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")
    elif form is not None:
        body = urllib.parse.urlencode(form).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")

    req = urllib.request.Request(url, data=body, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise HttpError(exc.code, exc.read().decode("utf-8", errors="replace")) from exc

    if not payload:
        return {}
    return json.loads(payload)


def build_url(base_url: str, path: str, params: dict[str, str] | None = None) -> str:
    url = base_url.rstrip("/") + "/" + path.lstrip("/")
    if params:
        url += "?" + urllib.parse.urlencode(params)
    return url

from __future__ import annotations

from html import escape


APP_NAME = "Rev360 QuickBooks E-Invoicing Connector"
CONTACT_EMAIL = "goke.adebisi@gmail.com"
COMPANY_NAME = "Bookeepa"


def legal_layout(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} | {escape(APP_NAME)}</title>
  <style>
    body {{
      margin: 0;
      color: #172033;
      background: #f7f8fb;
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.6;
    }}
    main {{
      max-width: 860px;
      margin: 0 auto;
      padding: 48px 20px 72px;
    }}
    article {{
      background: #fff;
      border: 1px solid #d9dee8;
      border-radius: 8px;
      padding: 32px;
    }}
    h1 {{
      margin-top: 0;
      line-height: 1.2;
    }}
    h2 {{
      margin-top: 32px;
      line-height: 1.25;
    }}
    p, li {{
      font-size: 16px;
    }}
    .updated {{
      color: #5c667a;
      margin-bottom: 28px;
    }}
  </style>
</head>
<body>
  <main>
    <article>
      {body}
    </article>
  </main>
</body>
</html>"""


def privacy_policy() -> str:
    return legal_layout(
        "Privacy Policy",
        f"""
<h1>Privacy Policy</h1>
<p class="updated">Last updated: June 13, 2026</p>
<p>{APP_NAME} is operated by {COMPANY_NAME}. This policy explains how the app handles information when connecting QuickBooks Online invoices to Rev360 e-invoicing services.</p>

<h2>Information We Collect</h2>
<p>The app may process business information needed to create or report invoices, including invoice numbers, invoice dates, customer names, customer contact details, tax identifiers, line items, totals, taxes, QuickBooks company identifiers, and Rev360 e-invoicing identifiers.</p>

<h2>How We Use Information</h2>
<p>We use this information only to connect to QuickBooks Online, prepare e-invoice payloads, submit invoices to Rev360 or related tax reporting services, check submission status, prevent duplicate submissions, and maintain basic integration records.</p>

<h2>QuickBooks Data</h2>
<p>When you authorize the app through QuickBooks, Intuit provides access tokens that allow the app to access approved QuickBooks Online accounting data. The app uses those tokens only for the integration features you enable.</p>

<h2>Sharing Information</h2>
<p>Invoice information may be sent to Rev360, FIRS-related e-invoicing services, Intuit QuickBooks Online, and service providers required to operate the integration. We do not sell personal information.</p>

<h2>Data Storage</h2>
<p>The app stores connection tokens, invoice sync records, and submission records so it can operate reliably and avoid duplicate invoice submissions. Production deployments should store secrets securely and restrict database access.</p>

<h2>Security</h2>
<p>We use reasonable technical safeguards to protect integration credentials and business data. No internet-connected system can be guaranteed completely secure.</p>

<h2>Data Retention</h2>
<p>We keep integration records only as long as needed for business, accounting, tax, troubleshooting, or legal purposes.</p>

<h2>Your Choices</h2>
<p>You may disconnect the app from QuickBooks Online through your Intuit account settings. You may also contact us to request deletion of integration records where legally permitted.</p>

<h2>Contact</h2>
<p>For privacy questions, contact us at {CONTACT_EMAIL}.</p>
""",
    )


def end_user_license_agreement() -> str:
    return legal_layout(
        "End-User License Agreement",
        f"""
<h1>End-User License Agreement</h1>
<p class="updated">Last updated: June 13, 2026</p>
<p>This End-User License Agreement governs your use of {APP_NAME}, operated by {COMPANY_NAME}. By using the app, you agree to these terms.</p>

<h2>Purpose</h2>
<p>The app is provided to help businesses connect QuickBooks Online invoice data with Rev360 e-invoicing and related reporting services.</p>

<h2>License</h2>
<p>We grant you a limited, non-exclusive, non-transferable license to use the app for your internal business purposes, subject to this agreement.</p>

<h2>Your Responsibilities</h2>
<p>You are responsible for the accuracy of invoice data, customer information, tax information, QuickBooks account access, Rev360 credentials, and any submissions made through the app.</p>

<h2>Third-Party Services</h2>
<p>The app connects with third-party services, including QuickBooks Online, Rev360, and tax reporting systems. Your use of those services is also governed by their own terms and policies.</p>

<h2>Restrictions</h2>
<p>You may not misuse the app, attempt unauthorized access, reverse engineer hosted services, interfere with system operation, or use the app for unlawful activity.</p>

<h2>No Tax or Legal Advice</h2>
<p>The app is a technical integration tool. It does not provide tax, accounting, or legal advice. You should confirm e-invoicing and tax compliance requirements with qualified professionals.</p>

<h2>Disclaimer</h2>
<p>The app is provided as is and as available. We do not guarantee uninterrupted operation, error-free submissions, or acceptance by third-party systems.</p>

<h2>Limitation of Liability</h2>
<p>To the fullest extent permitted by law, we are not liable for indirect, incidental, special, consequential, or punitive damages arising from your use of the app.</p>

<h2>Termination</h2>
<p>We may suspend or terminate access if the app is misused or if continued operation would create legal, security, or operational risk.</p>

<h2>Contact</h2>
<p>For questions about this agreement, contact us at {CONTACT_EMAIL}.</p>
""",
    )

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.config import Settings
from app.quickbooks import QuickBooksClient


def invoice_id(nrs_invoice: dict[str, Any]) -> str:
    value = nrs_invoice.get("id") or nrs_invoice.get("invoice_id") or nrs_invoice.get("invoiceNumber") or nrs_invoice.get("invoice_number")
    if not value:
        raise ValueError("NRS invoice is missing id/invoice_id/invoiceNumber.")
    return str(value)


def to_quickbooks_invoice(nrs_invoice: dict[str, Any], qb: QuickBooksClient, settings: Settings) -> dict[str, Any]:
    customer = nrs_invoice.get("customer") or {}
    customer_name = (
        customer.get("name")
        or nrs_invoice.get("customer_name")
        or nrs_invoice.get("store_name")
        or "NRS Customer"
    )
    customer_email = customer.get("email") or nrs_invoice.get("customer_email")
    customer_id = qb.ensure_customer(customer_name, customer_email)
    item_id = qb.ensure_item(settings.default_qb_item_name, settings.default_qb_income_account_name)

    lines = nrs_invoice.get("lines") or nrs_invoice.get("items") or []
    if not lines:
        lines = [{"description": "NRS invoice total", "amount": nrs_invoice.get("total") or nrs_invoice.get("total_amount") or 0}]

    qb_lines = []
    for line in lines:
        amount = money(line.get("amount") or line.get("total") or line.get("line_total") or 0)
        quantity = number(line.get("quantity") or line.get("qty") or 1)
        unit_price = money(line.get("unit_price") or line.get("price") or (amount / quantity if quantity else amount))
        qb_lines.append(
            {
                "DetailType": "SalesItemLineDetail",
                "Amount": float(amount),
                "Description": str(line.get("description") or line.get("name") or settings.default_qb_item_name),
                "SalesItemLineDetail": {
                    "ItemRef": {"value": item_id},
                    "Qty": float(quantity),
                    "UnitPrice": float(unit_price),
                },
            }
        )

    payload: dict[str, Any] = {
        "CustomerRef": {"value": customer_id},
        "Line": qb_lines,
        "PrivateNote": f"NRS Rev 360 invoice {invoice_id(nrs_invoice)}",
    }

    transaction_date = nrs_invoice.get("date") or nrs_invoice.get("invoice_date") or nrs_invoice.get("txn_date")
    due_date = nrs_invoice.get("due_date") or nrs_invoice.get("dueDate")
    if transaction_date:
        payload["TxnDate"] = str(transaction_date)[:10]
    if due_date:
        payload["DueDate"] = str(due_date)[:10]

    doc_number = nrs_invoice.get("invoice_number") or nrs_invoice.get("invoiceNumber")
    if doc_number:
        payload["DocNumber"] = str(doc_number)

    return payload


def money(value: Any) -> Decimal:
    return Decimal(str(value or "0")).quantize(Decimal("0.01"))


def number(value: Any) -> Decimal:
    return Decimal(str(value or "0"))

from __future__ import annotations

from typing import Any

from app.config import Settings
from app.http_client import build_url, request_json


class NrsClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def fetch_invoices(self, updated_since: str | None = None) -> list[dict[str, Any]]:
        if not self.settings.nrs_api_base_url:
            raise RuntimeError("NRS_API_BASE_URL is not configured. Use the webhook endpoint or add NRS API details.")

        params = {"updated_since": updated_since} if updated_since else None
        url = build_url(self.settings.nrs_api_base_url, self.settings.nrs_invoice_path, params)
        headers = {}
        if self.settings.nrs_api_token:
            headers["Authorization"] = f"Bearer {self.settings.nrs_api_token}"

        response = request_json("GET", url, headers=headers)
        if isinstance(response.get("invoices"), list):
            return response["invoices"]
        if isinstance(response.get("data"), list):
            return response["data"]
        if isinstance(response, list):
            return response
        raise RuntimeError("NRS invoice response did not include an invoices list.")

from __future__ import annotations

import base64
import time
import urllib.parse
from typing import Any

from app.config import Settings
from app.http_client import build_url, request_json
from app.storage import Storage


AUTH_URL = "https://appcenter.intuit.com/connect/oauth2"
TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
ACCOUNTING_SCOPE = "com.intuit.quickbooks.accounting"


class QuickBooksClient:
    def __init__(self, settings: Settings, storage: Storage) -> None:
        self.settings = settings
        self.storage = storage

    def authorization_url(self, state: str) -> str:
        params = {
            "client_id": self.settings.quickbooks_client_id,
            "response_type": "code",
            "scope": ACCOUNTING_SCOPE,
            "redirect_uri": self.settings.quickbooks_redirect_uri,
            "state": state,
        }
        return AUTH_URL + "?" + urllib.parse.urlencode(params)

    def exchange_code(self, code: str, realm_id: str) -> dict[str, Any]:
        token_data = self._token_request({"grant_type": "authorization_code", "code": code, "redirect_uri": self.settings.quickbooks_redirect_uri})
        return self._save_token_response(token_data, realm_id)

    def refresh_access_token(self) -> dict[str, Any]:
        stored = self.storage.get_quickbooks_tokens()
        if not stored:
            raise RuntimeError("QuickBooks is not connected yet.")
        token_data = self._token_request({"grant_type": "refresh_token", "refresh_token": stored["refresh_token"]})
        return self._save_token_response(token_data, stored["realm_id"])

    def create_invoice(self, invoice_payload: dict[str, Any]) -> dict[str, Any]:
        tokens = self._valid_tokens()
        url = self._company_url(tokens["realm_id"], "invoice")
        return request_json("POST", url, headers=self._auth_headers(tokens["access_token"]), data=invoice_payload)

    def query(self, query: str) -> dict[str, Any]:
        tokens = self._valid_tokens()
        url = self._company_url(tokens["realm_id"], "query", {"query": query})
        return request_json("GET", url, headers=self._auth_headers(tokens["access_token"]))

    def ensure_customer(self, display_name: str, email: str | None = None) -> str:
        safe_name = display_name.replace("\\", "\\\\").replace("'", "\\'")
        found = self.query(f"SELECT * FROM Customer WHERE DisplayName = '{safe_name}'")
        customers = found.get("QueryResponse", {}).get("Customer", [])
        if customers:
            return customers[0]["Id"]

        payload: dict[str, Any] = {"DisplayName": display_name}
        if email:
            payload["PrimaryEmailAddr"] = {"Address": email}
        tokens = self._valid_tokens()
        created = request_json("POST", self._company_url(tokens["realm_id"], "customer"), headers=self._auth_headers(tokens["access_token"]), data=payload)
        return created["Customer"]["Id"]

    def ensure_item(self, name: str, income_account_name: str) -> str:
        safe_name = name.replace("\\", "\\\\").replace("'", "\\'")
        found = self.query(f"SELECT * FROM Item WHERE Name = '{safe_name}'")
        items = found.get("QueryResponse", {}).get("Item", [])
        if items:
            return items[0]["Id"]

        account = self._find_income_account(income_account_name)
        tokens = self._valid_tokens()
        payload = {
            "Name": name,
            "Type": "Service",
            "IncomeAccountRef": {"value": account["Id"], "name": account.get("Name", income_account_name)},
        }
        created = request_json("POST", self._company_url(tokens["realm_id"], "item"), headers=self._auth_headers(tokens["access_token"]), data=payload)
        return created["Item"]["Id"]

    def _find_income_account(self, name: str) -> dict[str, Any]:
        safe_name = name.replace("\\", "\\\\").replace("'", "\\'")
        found = self.query(f"SELECT * FROM Account WHERE Name = '{safe_name}'")
        accounts = found.get("QueryResponse", {}).get("Account", [])
        if not accounts:
            raise RuntimeError(f"QuickBooks income account not found: {name}")
        return accounts[0]

    def _valid_tokens(self) -> dict[str, Any]:
        stored = self.storage.get_quickbooks_tokens()
        if not stored:
            raise RuntimeError("QuickBooks is not connected yet. Visit /auth/quickbooks/start first.")
        if int(stored["expires_at"]) <= int(time.time()) + 60:
            return self.refresh_access_token()
        return stored

    def _token_request(self, form: dict[str, str]) -> dict[str, Any]:
        credentials = f"{self.settings.quickbooks_client_id}:{self.settings.quickbooks_client_secret}".encode("utf-8")
        headers = {
            "Authorization": "Basic " + base64.b64encode(credentials).decode("ascii"),
            "Accept": "application/json",
        }
        return request_json("POST", TOKEN_URL, headers=headers, form=form)

    def _save_token_response(self, token_data: dict[str, Any], realm_id: str) -> dict[str, Any]:
        now = int(time.time())
        stored = self.storage.get_quickbooks_tokens()
        refresh_token = token_data.get("refresh_token") or (stored["refresh_token"] if stored else None)
        if not refresh_token:
            raise RuntimeError("QuickBooks token response did not include a refresh token.")
        saved = {
            "realm_id": realm_id,
            "access_token": token_data["access_token"],
            "refresh_token": refresh_token,
            "expires_at": now + int(token_data.get("expires_in", 3600)),
            "refresh_expires_at": now + int(token_data["x_refresh_token_expires_in"]) if token_data.get("x_refresh_token_expires_in") else None,
        }
        self.storage.save_quickbooks_tokens(saved)
        return saved

    def _company_url(self, realm_id: str, entity: str, params: dict[str, str] | None = None) -> str:
        query = dict(params or {})
        query["minorversion"] = self.settings.quickbooks_minor_version
        return build_url(self.settings.quickbooks_api_base_url, f"/v3/company/{realm_id}/{entity}", query)

    @staticmethod
    def _auth_headers(access_token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.config import Settings
from app.http_client import build_url, request_json
from app.mapping import invoice_id


class Rev360Client:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_irn(self, invoice: dict[str, Any]) -> str:
        source_id = invoice_id(invoice)
        invoice_date = invoice.get("date") or invoice.get("invoice_date") or invoice.get("issue_date") or date.today().isoformat()
        yyyymmdd = parse_date(invoice_date).strftime("%Y%m%d")
        return (
            self.settings.rev360_irn_template
            .replace("{{invoice_id}}", source_id)
            .replace("{{YYYYMMDD}}", yyyymmdd)
        )

    def build_einvoice_payload(self, invoice: dict[str, Any]) -> dict[str, Any]:
        irn = invoice.get("irn") or self.build_irn(invoice)
        issue_date = str(invoice.get("date") or invoice.get("invoice_date") or invoice.get("issue_date") or date.today().isoformat())[:10]
        due_date = invoice.get("due_date") or invoice.get("dueDate")
        customer = invoice.get("customer") or {}
        lines = invoice.get("lines") or invoice.get("items") or []

        if not lines:
            lines = [{"description": "Invoice total", "quantity": 1, "unit_price": invoice.get("total") or invoice.get("total_amount") or 0}]

        line_items = []
        subtotal = Decimal("0.00")
        tax_total = money(invoice.get("tax") or invoice.get("tax_total") or 0)

        for line in lines:
            quantity = number(line.get("quantity") or line.get("qty") or 1)
            unit_price = money(line.get("unit_price") or line.get("price") or line.get("amount") or 0)
            amount = money(line.get("amount") or line.get("total") or (quantity * unit_price))
            subtotal += amount
            line_items.append(
                {
                    "description": line.get("description") or line.get("name") or "Invoice line",
                    "quantity": float(quantity),
                    "unit_price": float(unit_price),
                    "amount": float(amount),
                    "tax_amount": float(money(line.get("tax") or line.get("tax_amount") or 0)),
                }
            )

        total = money(invoice.get("total") or invoice.get("total_amount") or (subtotal + tax_total))
        payload = {
            "irn": irn,
            "invoice_id": invoice_id(invoice),
            "invoice_number": invoice.get("invoice_number") or invoice.get("invoiceNumber") or invoice_id(invoice),
            "issue_date": issue_date,
            "currency": invoice.get("currency") or "NGN",
            "erp_name": self.settings.rev360_erp_name,
            "entity_id": self.settings.rev360_entity_id,
            "business_id": self.settings.rev360_business_id,
            "buyer": {
                "name": customer.get("name") or invoice.get("customer_name") or "Customer",
                "email": customer.get("email") or invoice.get("customer_email"),
                "tin": customer.get("tin") or customer.get("tax_id") or invoice.get("customer_tin"),
                "phone": customer.get("phone") or invoice.get("customer_phone"),
                "address": customer.get("address") or invoice.get("customer_address"),
            },
            "line_items": line_items,
            "totals": {
                "subtotal": float(subtotal),
                "tax_total": float(tax_total),
                "total": float(total),
            },
            "source": {
                "system": "QuickBooks",
                "raw_invoice": invoice,
            },
        }
        if due_date:
            payload["due_date"] = str(due_date)[:10]
        return payload

    def submit_einvoice(self, invoice: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
        payload = invoice.get("payload") if isinstance(invoice.get("payload"), dict) else self.build_einvoice_payload(invoice)
        if dry_run:
            return {"status": "dry_run", "payload": payload}

        response = request_json(
            "POST",
            build_url(self.settings.rev360_base_url, self.settings.rev360_submit_path),
            headers=self.headers(),
            data=payload,
        )
        return {"status": "submitted", "payload": payload, "response": response}

    def get_einvoice_status(self, irn: str) -> dict[str, Any]:
        path = self.settings.rev360_status_path.replace("{irn}", irn)
        response = request_json("GET", build_url(self.settings.rev360_report_base_url, path), headers=self.headers())
        return {"irn": irn, "response": response}

    def headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "X-API-Key": self.settings.rev360_api_key,
            "X-Client-Secret": self.settings.rev360_client_secret,
            "X-Entity-ID": self.settings.rev360_entity_id,
            "X-Business-ID": self.settings.rev360_business_id,
        }
        return {key: value for key, value in headers.items() if value}


def parse_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value)[:10]
    return datetime.strptime(text, "%Y-%m-%d").date()


def money(value: Any) -> Decimal:
    return Decimal(str(value or "0")).quantize(Decimal("0.01"))


def number(value: Any) -> Decimal:
    return Decimal(str(value or "0"))

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

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class Storage:
    def __init__(self, database_path: str) -> None:
        self.database_path = database_path
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS quickbooks_tokens (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    realm_id TEXT NOT NULL,
                    access_token TEXT NOT NULL,
                    refresh_token TEXT NOT NULL,
                    expires_at INTEGER NOT NULL,
                    refresh_expires_at INTEGER,
                    updated_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS invoice_syncs (
                    nrs_invoice_id TEXT PRIMARY KEY,
                    qb_invoice_id TEXT,
                    status TEXT NOT NULL,
                    source_payload TEXT NOT NULL,
                    error_message TEXT,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS rev360_submissions (
                    irn TEXT PRIMARY KEY,
                    invoice_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    request_payload TEXT NOT NULL,
                    response_payload TEXT,
                    error_message TEXT,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                );
                """
            )

    def save_quickbooks_tokens(self, token_data: dict[str, Any]) -> None:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO quickbooks_tokens (
                    id, realm_id, access_token, refresh_token, expires_at, refresh_expires_at, updated_at
                ) VALUES (1, ?, ?, ?, ?, ?, strftime('%s','now'))
                ON CONFLICT(id) DO UPDATE SET
                    realm_id = excluded.realm_id,
                    access_token = excluded.access_token,
                    refresh_token = excluded.refresh_token,
                    expires_at = excluded.expires_at,
                    refresh_expires_at = excluded.refresh_expires_at,
                    updated_at = excluded.updated_at
                """,
                (
                    token_data["realm_id"],
                    token_data["access_token"],
                    token_data["refresh_token"],
                    token_data["expires_at"],
                    token_data.get("refresh_expires_at"),
                ),
            )

    def get_quickbooks_tokens(self) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM quickbooks_tokens WHERE id = 1").fetchone()
        return dict(row) if row else None

    def get_invoice_sync(self, nrs_invoice_id: str) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM invoice_syncs WHERE nrs_invoice_id = ?", (nrs_invoice_id,)).fetchone()
        return dict(row) if row else None

    def record_invoice_sync(
        self,
        nrs_invoice_id: str,
        status: str,
        source_payload: dict[str, Any],
        qb_invoice_id: str | None = None,
        error_message: str | None = None,
    ) -> None:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO invoice_syncs (
                    nrs_invoice_id, qb_invoice_id, status, source_payload, error_message, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, strftime('%s','now'), strftime('%s','now'))
                ON CONFLICT(nrs_invoice_id) DO UPDATE SET
                    qb_invoice_id = excluded.qb_invoice_id,
                    status = excluded.status,
                    source_payload = excluded.source_payload,
                    error_message = excluded.error_message,
                    updated_at = excluded.updated_at
                """,
                (nrs_invoice_id, qb_invoice_id, status, json.dumps(source_payload), error_message),
            )

    def record_rev360_submission(
        self,
        irn: str,
        invoice_id: str,
        status: str,
        request_payload: dict[str, Any],
        response_payload: Any | None = None,
        error_message: str | None = None,
    ) -> None:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO rev360_submissions (
                    irn, invoice_id, status, request_payload, response_payload, error_message, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, strftime('%s','now'), strftime('%s','now'))
                ON CONFLICT(irn) DO UPDATE SET
                    invoice_id = excluded.invoice_id,
                    status = excluded.status,
                    request_payload = excluded.request_payload,
                    response_payload = excluded.response_payload,
                    error_message = excluded.error_message,
                    updated_at = excluded.updated_at
                """,
                (
                    irn,
                    invoice_id,
                    status,
                    json.dumps(request_payload),
                    json.dumps(response_payload) if response_payload is not None else None,
                    error_message,
                ),
            )

from __future__ import annotations

from typing import Any

from app.config import Settings
from app.mapping import invoice_id, to_quickbooks_invoice
from app.nrs import NrsClient
from app.quickbooks import QuickBooksClient
from app.storage import Storage


class InvoiceSyncService:
    def __init__(self, settings: Settings, storage: Storage, qb: QuickBooksClient, nrs: NrsClient) -> None:
        self.settings = settings
        self.storage = storage
        self.qb = qb
        self.nrs = nrs

    def sync_one(self, nrs_invoice: dict[str, Any]) -> dict[str, Any]:
        nrs_id = invoice_id(nrs_invoice)
        existing = self.storage.get_invoice_sync(nrs_id)
        if existing and existing["status"] == "synced":
            return {"status": "skipped", "reason": "already_synced", "nrs_invoice_id": nrs_id, "qb_invoice_id": existing["qb_invoice_id"]}

        try:
            qb_payload = to_quickbooks_invoice(nrs_invoice, self.qb, self.settings)
            created = self.qb.create_invoice(qb_payload)
            qb_invoice = created.get("Invoice", {})
            qb_invoice_id = qb_invoice.get("Id")
            self.storage.record_invoice_sync(nrs_id, "synced", nrs_invoice, qb_invoice_id=qb_invoice_id)
            return {"status": "synced", "nrs_invoice_id": nrs_id, "qb_invoice_id": qb_invoice_id}
        except Exception as exc:
            self.storage.record_invoice_sync(nrs_id, "failed", nrs_invoice, error_message=str(exc))
            raise

    def sync_from_nrs(self, updated_since: str | None = None) -> dict[str, Any]:
        invoices = self.nrs.fetch_invoices(updated_since)
        results = []
        for invoice in invoices:
            results.append(self.sync_one(invoice))
        return {"count": len(results), "results": results}

"""NRS Rev 360 to QuickBooks invoice sync service."""
