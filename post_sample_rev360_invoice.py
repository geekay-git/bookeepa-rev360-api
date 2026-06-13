from __future__ import annotations

import json
import urllib.request


sample_invoice = {
    "id": "INV00123",
    "invoice_number": "INV00123",
    "date": "2026-06-12",
    "due_date": "2026-06-19",
    "currency": "NGN",
    "customer": {
        "name": "Sample Buyer Ltd",
        "email": "buyer@example.com",
        "tin": "12345678-0001",
        "phone": "+2348000000000",
        "address": "Lagos, Nigeria",
    },
    "lines": [
        {"description": "Retail goods", "quantity": 2, "unit_price": 5000, "amount": 10000, "tax_amount": 750},
    ],
    "tax_total": 750,
    "total_amount": 10750,
}

body = json.dumps(sample_invoice).encode("utf-8")
request = urllib.request.Request(
    "http://localhost:8080/rev360/e-invoices/preview",
    data=body,
    method="POST",
    headers={"Content-Type": "application/json"},
)

with urllib.request.urlopen(request) as response:
    print(response.read().decode("utf-8"))
