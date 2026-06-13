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
