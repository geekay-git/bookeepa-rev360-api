from __future__ import annotations

import json
import urllib.request


sample_invoice = {
    "id": "NRS-1001",
    "invoice_number": "NRS-1001",
    "date": "2026-06-13",
    "due_date": "2026-06-20",
    "customer": {"name": "Sample Retail Customer", "email": "customer@example.com"},
    "lines": [
        {"description": "Retail sales", "quantity": 1, "unit_price": 125.00, "amount": 125.00},
        {"description": "Tax", "quantity": 1, "unit_price": 10.00, "amount": 10.00},
    ],
}

body = json.dumps(sample_invoice).encode("utf-8")
request = urllib.request.Request(
    "http://localhost:8080/webhooks/nrs/invoice",
    data=body,
    method="POST",
    headers={"Content-Type": "application/json", "X-NRS-Webhook-Secret": "replace-with-shared-secret"},
)

with urllib.request.urlopen(request) as response:
    print(response.read().decode("utf-8"))
