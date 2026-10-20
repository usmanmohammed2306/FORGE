"""Local development registry. PostgreSQL becomes the release backend in S03."""

import sqlite3
from pathlib import Path
from typing import Any


class RunRegistry:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL CHECK(status IN ('running', 'complete', 'failed')),
                    created_at TEXT NOT NULL,
                    config_digest TEXT NOT NULL,
                    config_ref TEXT NOT NULL,
                    report_ref TEXT,
                    passport_ref TEXT,
                    error TEXT
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def start(self, run_id: str, created_at: str, config_digest: str, config_ref: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO runs(run_id,status,created_at,config_digest,config_ref) "
                "VALUES (?, 'running', ?, ?, ?)",
                (run_id, created_at, config_digest, config_ref),
            )

    def complete(self, run_id: str, report_ref: str, passport_ref: str) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE runs SET status='complete', report_ref=?, passport_ref=? "
                "WHERE run_id=? AND status='running'",
                (report_ref, passport_ref, run_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("run does not exist or is not running")

    def fail(self, run_id: str, reason: str) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE runs SET status='failed', error=? WHERE run_id=? AND status='running'",
                (reason, run_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("run does not exist or is not running")

    def get(self, run_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(f"unknown run: {run_id}")
        return dict(row)

    def list(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM runs ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]
