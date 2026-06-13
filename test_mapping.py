from __future__ import annotations

import unittest

from app.mapping import invoice_id, to_quickbooks_invoice


class FakeQuickBooks:
    def ensure_customer(self, display_name: str, email: str | None = None) -> str:
        self.customer_name = display_name
        self.customer_email = email
        return "123"

    def ensure_item(self, name: str, income_account_name: str) -> str:
        self.item_name = name
        self.income_account_name = income_account_name
        return "456"


class FakeSettings:
    default_qb_item_name = "NRS Sales"
    default_qb_income_account_name = "Sales"


class MappingTests(unittest.TestCase):
    def test_invoice_id_accepts_common_fields(self) -> None:
        self.assertEqual(invoice_id({"invoiceNumber": "INV-1"}), "INV-1")

    def test_maps_invoice_to_quickbooks_payload(self) -> None:
        qb = FakeQuickBooks()
        payload = to_quickbooks_invoice(
            {
                "id": "NRS-1",
                "invoice_number": "NRS-1",
                "date": "2026-06-13",
                "customer": {"name": "Corner Store", "email": "owner@example.com"},
                "lines": [{"description": "Sales", "quantity": 2, "unit_price": 5, "amount": 10}],
            },
            qb,
            FakeSettings(),
        )

        self.assertEqual(payload["CustomerRef"]["value"], "123")
        self.assertEqual(payload["DocNumber"], "NRS-1")
        self.assertEqual(payload["TxnDate"], "2026-06-13")
        self.assertEqual(payload["Line"][0]["Amount"], 10.0)
        self.assertEqual(payload["Line"][0]["SalesItemLineDetail"]["ItemRef"]["value"], "456")


if __name__ == "__main__":
    unittest.main()
