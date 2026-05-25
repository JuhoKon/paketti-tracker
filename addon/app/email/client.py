"""Async IMAP email client for Paketti Tracker (standalone, no HA dependency)."""

from __future__ import annotations

import contextlib
import email
import logging
from email.message import Message

import aioimaplib

logger = logging.getLogger(__name__)


class EmailClientError(Exception):
    """Raised on IMAP connection/operation errors."""


class EmailClient:
    """Async IMAP client for fetching emails."""

    def __init__(
        self,
        server: str,
        port: int,
        username: str,
        password: str,
        folder: str = "INBOX",
    ) -> None:
        """Initialize the email client."""
        self._server = server
        self._port = port
        self._username = username
        self._password = password
        self._folder = folder
        self._client: aioimaplib.IMAP4_SSL | None = None

    async def connect(self) -> None:
        """Connect and authenticate to the IMAP server."""
        try:
            self._client = aioimaplib.IMAP4_SSL(
                host=self._server, port=self._port
            )
            await self._client.wait_hello_from_server()
            response = await self._client.login(self._username, self._password)
            if response.result != "OK":
                raise EmailClientError(f"Login failed: {response.lines}")
        except (OSError, TimeoutError) as exc:
            raise EmailClientError(f"Connection failed: {exc}") from exc

    async def disconnect(self) -> None:
        """Disconnect from the IMAP server."""
        if self._client:
            with contextlib.suppress(Exception):
                await self._client.logout()
            self._client = None

    async def search_recent(self, days: int = 7) -> list[str]:
        """Search for emails from the last N days. Returns message UIDs."""
        if not self._client:
            raise EmailClientError("Not connected")

        from datetime import UTC, datetime, timedelta

        since_date = (datetime.now(UTC) - timedelta(days=days)).strftime("%d-%b-%Y")

        await self._client.select(self._folder)
        response = await self._client.uid("search", None, f"SINCE {since_date}")

        if response.result != "OK":
            logger.warning("IMAP search failed: %s", response.lines)
            return []

        # response.lines[0] contains space-separated UIDs.
        uids_line = response.lines[0] if response.lines else ""
        if not uids_line or uids_line == b"":
            return []

        if isinstance(uids_line, bytes):
            uids_line = uids_line.decode()

        return uids_line.strip().split() if uids_line.strip() else []

    async def fetch_message(self, uid: str) -> Message | None:
        """Fetch a single email message by UID."""
        if not self._client:
            raise EmailClientError("Not connected")

        response = await self._client.uid("fetch", uid, "(RFC822)")
        if response.result != "OK":
            logger.warning("Failed to fetch message %s", uid)
            return None

        # aioimaplib returns data as list of (header, body) tuples.
        for item in response.lines:
            if isinstance(item, bytes) and item:
                return email.message_from_bytes(item)

        return None

    async def fetch_messages(self, uids: list[str]) -> list[Message]:
        """Fetch multiple messages by UID."""
        messages: list[Message] = []
        for uid in uids:
            msg = await self.fetch_message(uid)
            if msg:
                messages.append(msg)
        return messages

    async def test_connection(self) -> bool:
        """Test the IMAP connection. Returns True if successful."""
        try:
            await self.connect()
            await self.disconnect()
            return True
        except EmailClientError:
            return False
