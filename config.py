from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    app_host: str
    app_port: int
    app_base_url: str
    database_path: str
    quickbooks_environment: str
    quickbooks_client_id: str
    quickbooks_client_secret: str
    quickbooks_redirect_uri: str
    quickbooks_minor_version: str
    nrs_api_base_url: str
    nrs_api_token: str
    nrs_invoice_path: str
    nrs_webhook_secret: str
    rev360_base_url: str
    rev360_report_base_url: str
    rev360_erp_name: str
    rev360_entity_id: str
    rev360_business_id: str
    rev360_api_key: str
    rev360_client_secret: str
    rev360_irn_template: str
    rev360_submit_path: str
    rev360_status_path: str
    default_qb_item_name: str
    default_qb_income_account_name: str

    @property
    def quickbooks_api_base_url(self) -> str:
        return "https://sandbox-quickbooks.api.intuit.com" if self.quickbooks_environment == "sandbox" else "https://quickbooks.api.intuit.com"


def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        app_host=os.getenv("APP_HOST", "127.0.0.1"),
        app_port=int(os.getenv("APP_PORT", "8080")),
        app_base_url=os.getenv("APP_BASE_URL", "http://localhost:8080"),
        database_path=os.getenv("APP_DATABASE_PATH", "work/integration.sqlite3"),
        quickbooks_environment=os.getenv("QUICKBOOKS_ENVIRONMENT", "sandbox"),
        quickbooks_client_id=os.getenv("QUICKBOOKS_CLIENT_ID", ""),
        quickbooks_client_secret=os.getenv("QUICKBOOKS_CLIENT_SECRET", ""),
        quickbooks_redirect_uri=os.getenv("QUICKBOOKS_REDIRECT_URI", "http://localhost:8080/auth/quickbooks/callback"),
        quickbooks_minor_version=os.getenv("QUICKBOOKS_MINOR_VERSION", "75"),
        nrs_api_base_url=os.getenv("NRS_API_BASE_URL", ""),
        nrs_api_token=os.getenv("NRS_API_TOKEN", ""),
        nrs_invoice_path=os.getenv("NRS_INVOICE_PATH", "/invoices"),
        nrs_webhook_secret=os.getenv("NRS_WEBHOOK_SECRET", ""),
        rev360_base_url=os.getenv("REV360_BASE_URL", "https://eivc-k6z6d.ondigitalocean.app"),
        rev360_report_base_url=os.getenv("REV360_REPORT_BASE_URL", "https://api.firsmbs.com"),
        rev360_erp_name=os.getenv("REV360_ERP_NAME", "QuickBooks"),
        rev360_entity_id=os.getenv("REV360_ENTITY_ID", ""),
        rev360_business_id=os.getenv("REV360_BUSINESS_ID", ""),
        rev360_api_key=os.getenv("REV360_API_KEY", ""),
        rev360_client_secret=os.getenv("REV360_CLIENT_SECRET", ""),
        rev360_irn_template=os.getenv("REV360_IRN_TEMPLATE", "{{invoice_id}}-1A57E861-{{YYYYMMDD}}"),
        rev360_submit_path=os.getenv("REV360_SUBMIT_PATH", "/api/v1/e-invoices"),
        rev360_status_path=os.getenv("REV360_STATUS_PATH", "/api/v1/e-invoices/{irn}"),
        default_qb_item_name=os.getenv("DEFAULT_QB_ITEM_NAME", "NRS Sales"),
        default_qb_income_account_name=os.getenv("DEFAULT_QB_INCOME_ACCOUNT_NAME", "Sales"),
    )
