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
