from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class Storage:
    def __init__(self, database_path: str) -> None:
        self.database_path = database_path
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS quickbooks_tokens (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    realm_id TEXT NOT NULL,
                    access_token TEXT NOT NULL,
                    refresh_token TEXT NOT NULL,
                    expires_at INTEGER NOT NULL,
                    refresh_expires_at INTEGER,
                    updated_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS invoice_syncs (
                    nrs_invoice_id TEXT PRIMARY KEY,
                    qb_invoice_id TEXT,
                    status TEXT NOT NULL,
                    source_payload TEXT NOT NULL,
                    error_message TEXT,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS rev360_submissions (
                    irn TEXT PRIMARY KEY,
                    invoice_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    request_payload TEXT NOT NULL,
                    response_payload TEXT,
                    error_message TEXT,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                );
                """
            )

    def save_quickbooks_tokens(self, token_data: dict[str, Any]) -> None:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO quickbooks_tokens (
                    id, realm_id, access_token, refresh_token, expires_at, refresh_expires_at, updated_at
                ) VALUES (1, ?, ?, ?, ?, ?, strftime('%s','now'))
                ON CONFLICT(id) DO UPDATE SET
                    realm_id = excluded.realm_id,
                    access_token = excluded.access_token,
                    refresh_token = excluded.refresh_token,
                    expires_at = excluded.expires_at,
                    refresh_expires_at = excluded.refresh_expires_at,
                    updated_at = excluded.updated_at
                """,
                (
                    token_data["realm_id"],
                    token_data["access_token"],
                    token_data["refresh_token"],
                    token_data["expires_at"],
                    token_data.get("refresh_expires_at"),
                ),
            )

    def get_quickbooks_tokens(self) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM quickbooks_tokens WHERE id = 1").fetchone()
        return dict(row) if row else None

    def get_invoice_sync(self, nrs_invoice_id: str) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM invoice_syncs WHERE nrs_invoice_id = ?", (nrs_invoice_id,)).fetchone()
        return dict(row) if row else None

    def record_invoice_sync(
        self,
        nrs_invoice_id: str,
        status: str,
        source_payload: dict[str, Any],
        qb_invoice_id: str | None = None,
        error_message: str | None = None,
    ) -> None:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO invoice_syncs (
                    nrs_invoice_id, qb_invoice_id, status, source_payload, error_message, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, strftime('%s','now'), strftime('%s','now'))
                ON CONFLICT(nrs_invoice_id) DO UPDATE SET
                    qb_invoice_id = excluded.qb_invoice_id,
                    status = excluded.status,
                    source_payload = excluded.source_payload,
                    error_message = excluded.error_message,
                    updated_at = excluded.updated_at
                """,
                (nrs_invoice_id, qb_invoice_id, status, json.dumps(source_payload), error_message),
            )

    def record_rev360_submission(
        self,
        irn: str,
        invoice_id: str,
        status: str,
        request_payload: dict[str, Any],
        response_payload: Any | None = None,
        error_message: str | None = None,
    ) -> None:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO rev360_submissions (
                    irn, invoice_id, status, request_payload, response_payload, error_message, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, strftime('%s','now'), strftime('%s','now'))
                ON CONFLICT(irn) DO UPDATE SET
                    invoice_id = excluded.invoice_id,
                    status = excluded.status,
                    request_payload = excluded.request_payload,
                    response_payload = excluded.response_payload,
                    error_message = excluded.error_message,
                    updated_at = excluded.updated_at
                """,
                (
                    irn,
                    invoice_id,
                    status,
                    json.dumps(request_payload),
                    json.dumps(response_payload) if response_payload is not None else None,
                    error_message,
                ),
            )
