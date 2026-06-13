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
