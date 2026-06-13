from __future__ import annotations

import unittest

from app.rev360 import Rev360Client


class FakeSettings:
    rev360_irn_template = "{{invoice_id}}-1A57E861-{{YYYYMMDD}}"
    rev360_erp_name = "QuickBooks"
    rev360_entity_id = "entity"
    rev360_business_id = "business"
    rev360_api_key = "api-key"
    rev360_client_secret = "secret"
    rev360_base_url = "https://example.com"
    rev360_report_base_url = "https://reports.example.com"
    rev360_submit_path = "/submit"
    rev360_status_path = "/status/{irn}"


class Rev360Tests(unittest.TestCase):
    def test_builds_irn_from_template(self) -> None:
        client = Rev360Client(FakeSettings())
        self.assertEqual(client.build_irn({"id": "INV00123", "date": "2026-06-12"}), "INV00123-1A57E861-20260612")

    def test_builds_einvoice_payload(self) -> None:
        client = Rev360Client(FakeSettings())
        payload = client.build_einvoice_payload(
            {
                "id": "INV00123",
                "date": "2026-06-12",
                "customer": {"name": "Buyer", "tin": "TIN"},
                "lines": [{"description": "Goods", "quantity": 2, "unit_price": 10, "amount": 20}],
                "tax_total": 1.5,
            }
        )

        self.assertEqual(payload["irn"], "INV00123-1A57E861-20260612")
        self.assertEqual(payload["buyer"]["name"], "Buyer")
        self.assertEqual(payload["totals"]["total"], 21.5)
        self.assertEqual(payload["line_items"][0]["amount"], 20.0)


if __name__ == "__main__":
    unittest.main()
