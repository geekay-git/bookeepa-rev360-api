# Rev360 E-Invoicing and QuickBooks Invoice API

Small API service that receives invoice data, prepares it for Rev360 e-invoicing, and can also create matching invoices in QuickBooks Online.

The Rev360 base URLs and credential fields are configurable through `.env`. The exact Rev360 submit/status endpoint paths are also configurable because the portal screenshot provides the base URLs and credentials, but not the final endpoint path.

## What This Service Does

- Builds a Rev360 IRN using `{{invoice_id}}-1A57E861-{{YYYYMMDD}}`.
- Converts invoice JSON into a Rev360 e-invoice payload.
- Submits e-invoices to the configured Rev360 endpoint.
- Reads e-invoice status from the configured Rev360 report endpoint.
- Stores Rev360 submission attempts in local SQLite.
- Connects to QuickBooks Online using OAuth 2.0.
- Stores QuickBooks refresh/access tokens in local SQLite.
- Accepts NRS invoices at `POST /webhooks/nrs/invoice`.
- Optionally pulls NRS invoices from `NRS_API_BASE_URL`.
- Maps NRS invoice data into QuickBooks invoice payloads.
- Prevents duplicate syncs using the NRS invoice ID.
- Exposes `POST /sync/invoices` for manual sync.

## Quick Start

1. Copy `.env.example` to `.env` and fill in your Rev360 and QuickBooks credentials.
2. Run the API:

```powershell
& 'C:\Users\HP\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m app.server
```

3. Check the Rev360 config:

```text
http://localhost:8080/rev360/config
```

4. Preview a Rev360 e-invoice payload:

```powershell
& 'C:\Users\HP\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\post_sample_rev360_invoice.py
```

5. Open this URL in your browser to connect QuickBooks:

```text
http://localhost:8080/auth/quickbooks/start
```

6. Configure NRS Rev 360 to send invoices to:

```text
http://your-server.com/webhooks/nrs/invoice
```

For local testing, post a sample invoice:

```powershell
& 'C:\Users\HP\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\post_sample_invoice.py
```

## Required QuickBooks Setup

Create an app in the Intuit Developer Portal and enable the QuickBooks Online Accounting scope.

Set the redirect URI in Intuit to:

```text
http://localhost:8080/auth/quickbooks/callback
```

For production, replace `localhost` with your HTTPS domain.

## NRS Rev 360 Details Needed

Ask NRS for one of these:

- A webhook feature that posts invoice JSON when an invoice is created or updated.
- An invoice API endpoint, API key/token, pagination rules, and invoice schema.
- A CSV export location if API/webhooks are not available.

Once you have the exact NRS schema, update `app/mapping.py` if field names differ.

## Main Endpoints

- `GET /health` checks service status.
- `GET /legal/eula` shows the end-user license agreement page.
- `GET /legal/privacy` shows the privacy policy page.
- `GET /rev360/config` checks Rev360 connection settings without exposing secrets.
- `POST /rev360/e-invoices/preview` builds a Rev360 e-invoice payload without submitting it.
- `POST /rev360/e-invoices` submits an e-invoice to Rev360.
- `GET /rev360/e-invoices/{irn}` checks e-invoice status through the report base URL.
- `GET /auth/quickbooks/start` redirects you to QuickBooks authorization.
- `GET /auth/quickbooks/callback` receives QuickBooks OAuth callback.
- `POST /webhooks/nrs/invoice` receives a single NRS invoice and syncs it.
- `POST /sync/invoices` pulls invoices from NRS and syncs them.

## Rev360 Configuration

Use these `.env` values:

```text
REV360_BASE_URL=https://eivc-k6z6d.ondigitalocean.app
REV360_REPORT_BASE_URL=https://api.firsmbs.com
REV360_ERP_NAME=QuickBooks
REV360_ENTITY_ID=your-entity-id
REV360_BUSINESS_ID=your-business-id
REV360_API_KEY=your-api-key
REV360_CLIENT_SECRET=your-client-secret
REV360_IRN_TEMPLATE={{invoice_id}}-1A57E861-{{YYYYMMDD}}
REV360_SUBMIT_PATH=/api/v1/e-invoices
REV360_STATUS_PATH=/api/v1/e-invoices/{irn}
```

If Rev360 gives you a different submit or report path, update `REV360_SUBMIT_PATH` and `REV360_STATUS_PATH`; the code does not need to change.

To test the full submission route without sending to Rev360, call:

```text
POST /rev360/e-invoices?dry_run=true
```

## QuickBooks App Legal URLs

The QuickBooks Developer Portal requires public HTTPS links for the EULA and privacy policy. After deploying this API, use:

```text
https://your-api-domain.com/legal/eula
https://your-api-domain.com/legal/privacy
```

For local preview only, use:

```text
http://localhost:8080/legal/eula
http://localhost:8080/legal/privacy
```

Before publishing, update `APP_NAME`, `COMPANY_NAME`, and `CONTACT_EMAIL` in `app/legal_pages.py`.

## Notes

This is a starter integration, not the final production hardening pass. Before going live, add HTTPS, a real secrets manager, request authentication for NRS webhooks, monitoring, and a background job scheduler.
