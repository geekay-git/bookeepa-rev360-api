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
