from __future__ import annotations

from html import escape


APP_NAME = "Rev360 QuickBooks E-Invoicing Connector"
CONTACT_EMAIL = "goke.adebisi@gmail.com"
COMPANY_NAME = "Bookeepa"


def legal_layout(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} | {escape(APP_NAME)}</title>
  <style>
    body {{
      margin: 0;
      color: #172033;
      background: #f7f8fb;
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.6;
    }}
    main {{
      max-width: 860px;
      margin: 0 auto;
      padding: 48px 20px 72px;
    }}
    article {{
      background: #fff;
      border: 1px solid #d9dee8;
      border-radius: 8px;
      padding: 32px;
    }}
    h1 {{
      margin-top: 0;
      line-height: 1.2;
    }}
    h2 {{
      margin-top: 32px;
      line-height: 1.25;
    }}
    p, li {{
      font-size: 16px;
    }}
    .updated {{
      color: #5c667a;
      margin-bottom: 28px;
    }}
  </style>
</head>
<body>
  <main>
    <article>
      {body}
    </article>
  </main>
</body>
</html>"""


def privacy_policy() -> str:
    return legal_layout(
        "Privacy Policy",
        f"""
<h1>Privacy Policy</h1>
<p class="updated">Last updated: June 13, 2026</p>
<p>{APP_NAME} is operated by {COMPANY_NAME}. This policy explains how the app handles information when connecting QuickBooks Online invoices to Rev360 e-invoicing services.</p>

<h2>Information We Collect</h2>
<p>The app may process business information needed to create or report invoices, including invoice numbers, invoice dates, customer names, customer contact details, tax identifiers, line items, totals, taxes, QuickBooks company identifiers, and Rev360 e-invoicing identifiers.</p>

<h2>How We Use Information</h2>
<p>We use this information only to connect to QuickBooks Online, prepare e-invoice payloads, submit invoices to Rev360 or related tax reporting services, check submission status, prevent duplicate submissions, and maintain basic integration records.</p>

<h2>QuickBooks Data</h2>
<p>When you authorize the app through QuickBooks, Intuit provides access tokens that allow the app to access approved QuickBooks Online accounting data. The app uses those tokens only for the integration features you enable.</p>

<h2>Sharing Information</h2>
<p>Invoice information may be sent to Rev360, FIRS-related e-invoicing services, Intuit QuickBooks Online, and service providers required to operate the integration. We do not sell personal information.</p>

<h2>Data Storage</h2>
<p>The app stores connection tokens, invoice sync records, and submission records so it can operate reliably and avoid duplicate invoice submissions. Production deployments should store secrets securely and restrict database access.</p>

<h2>Security</h2>
<p>We use reasonable technical safeguards to protect integration credentials and business data. No internet-connected system can be guaranteed completely secure.</p>

<h2>Data Retention</h2>
<p>We keep integration records only as long as needed for business, accounting, tax, troubleshooting, or legal purposes.</p>

<h2>Your Choices</h2>
<p>You may disconnect the app from QuickBooks Online through your Intuit account settings. You may also contact us to request deletion of integration records where legally permitted.</p>

<h2>Contact</h2>
<p>For privacy questions, contact us at {CONTACT_EMAIL}.</p>
""",
    )


def end_user_license_agreement() -> str:
    return legal_layout(
        "End-User License Agreement",
        f"""
<h1>End-User License Agreement</h1>
<p class="updated">Last updated: June 13, 2026</p>
<p>This End-User License Agreement governs your use of {APP_NAME}, operated by {COMPANY_NAME}. By using the app, you agree to these terms.</p>

<h2>Purpose</h2>
<p>The app is provided to help businesses connect QuickBooks Online invoice data with Rev360 e-invoicing and related reporting services.</p>

<h2>License</h2>
<p>We grant you a limited, non-exclusive, non-transferable license to use the app for your internal business purposes, subject to this agreement.</p>

<h2>Your Responsibilities</h2>
<p>You are responsible for the accuracy of invoice data, customer information, tax information, QuickBooks account access, Rev360 credentials, and any submissions made through the app.</p>

<h2>Third-Party Services</h2>
<p>The app connects with third-party services, including QuickBooks Online, Rev360, and tax reporting systems. Your use of those services is also governed by their own terms and policies.</p>

<h2>Restrictions</h2>
<p>You may not misuse the app, attempt unauthorized access, reverse engineer hosted services, interfere with system operation, or use the app for unlawful activity.</p>

<h2>No Tax or Legal Advice</h2>
<p>The app is a technical integration tool. It does not provide tax, accounting, or legal advice. You should confirm e-invoicing and tax compliance requirements with qualified professionals.</p>

<h2>Disclaimer</h2>
<p>The app is provided as is and as available. We do not guarantee uninterrupted operation, error-free submissions, or acceptance by third-party systems.</p>

<h2>Limitation of Liability</h2>
<p>To the fullest extent permitted by law, we are not liable for indirect, incidental, special, consequential, or punitive damages arising from your use of the app.</p>

<h2>Termination</h2>
<p>We may suspend or terminate access if the app is misused or if continued operation would create legal, security, or operational risk.</p>

<h2>Contact</h2>
<p>For questions about this agreement, contact us at {CONTACT_EMAIL}.</p>
""",
    )
