"""Data access layer for key-value settings."""

from __future__ import annotations

import json
from typing import Any

from app.database import Database


# Default values for settings
DEFAULTS: dict[str, Any] = {
    "poll_interval_minutes": 60,
    "email_poll_interval_minutes": 30,
    "notifications": json.dumps({
        "enabled": True,
        "devices": [],
        "triggers": [
            {"event_type": "delivered", "enabled": True},
            {"event_type": "in_transit", "enabled": True},
            {"event_type": "status_change", "enabled": False},
        ],
    }),
    "email": json.dumps({
        "enabled": False,
        "host": "",
        "port": 993,
        "username": "",
        "password": "",
        "folder": "INBOX",
        "auto_add": False,
    }),
}


class SettingsRepository:
    """Repository for key-value settings stored in the settings table."""

    def __init__(self, db: Database) -> None:
        self._db = db

    async def get(self, key: str) -> str | None:
        """Get a setting value by key. Returns None if not set."""
        row = await self._db.fetchone(
            "SELECT value FROM settings WHERE key = ?", (key,)
        )
        if row:
            return row["value"]
        return DEFAULTS.get(key)

    async def get_int(self, key: str, default: int = 0) -> int:
        """Get a setting as an integer."""
        value = await self.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    async def get_json(self, key: str) -> Any:
        """Get a setting as parsed JSON."""
        value = await self.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None

    async def set(self, key: str, value: str) -> None:
        """Set a setting value (upsert)."""
        await self._db.execute(
            """
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
        await self._db.commit()

    async def set_json(self, key: str, value: Any) -> None:
        """Set a setting as JSON."""
        await self.set(key, json.dumps(value))

    async def delete(self, key: str) -> None:
        """Delete a setting."""
        await self._db.execute("DELETE FROM settings WHERE key = ?", (key,))
        await self._db.commit()

    async def get_all(self) -> dict[str, str]:
        """Get all settings as a dict."""
        rows = await self._db.fetchall("SELECT key, value FROM settings")
        result = dict(DEFAULTS)
        for row in rows:
            result[row["key"]] = row["value"]
        return result
