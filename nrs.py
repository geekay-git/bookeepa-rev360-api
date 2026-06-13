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
