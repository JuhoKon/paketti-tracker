"""Tests for email parser and email service."""

from __future__ import annotations

from email.message import Message
from unittest.mock import AsyncMock, patch

import pytest

from app.config import Settings
from app.database import Database
from app.db.repository import PackageRepository
from app.email.parser import (
    DiscoveredPackage,
    parse_email,
    _detect_vendor_from_sender,
    _extract_tracking_ids,
)
from app.services.email_service import EmailService


# -- Parser tests ---


def _make_message(subject: str, sender: str, body: str) -> Message:
    """Create a simple email.message.Message for testing."""
    msg = Message()
    msg["Subject"] = subject
    msg["From"] = sender
    msg.set_payload(body.encode("utf-8"))
    msg.set_type("text/plain")
    msg.set_charset("utf-8")
    return msg


class TestEmailParser:
    """Tests for the email parser."""

    def test_detect_posti_sender(self):
        """Detect Posti from sender."""
        assert _detect_vendor_from_sender("noreply@posti.fi") == "posti"
        assert _detect_vendor_from_sender("info@posti.com") == "posti"  # @posti. pattern matches
        assert _detect_vendor_from_sender("random@example.com") is None

    def test_detect_postnord_sender(self):
        """Detect Postnord from sender."""
        assert _detect_vendor_from_sender("noreply@postnord.fi") == "postnord"

    def test_detect_matkahuolto_sender(self):
        """Detect Matkahuolto from sender."""
        assert _detect_vendor_from_sender("info@matkahuolto.fi") == "matkahuolto"

    def test_extract_posti_tracking_id(self):
        """Extract Posti tracking ID from text."""
        text = "Your tracking code is JJFI60773420139193970"
        results = _extract_tracking_ids(text, "posti")
        assert len(results) == 1
        assert results[0] == ("JJFI60773420139193970", "posti")

    def test_extract_posti_generic_format(self):
        """Extract generic Posti format (XX + 9 digits + FI)."""
        text = "Tracking: RA123456789FI"
        results = _extract_tracking_ids(text, "posti")
        assert len(results) == 1
        assert results[0][0] == "RA123456789FI"

    def test_extract_matkahuolto_id(self):
        """Extract Matkahuolto tracking ID."""
        text = "Seurantakoodi: MH12345678"
        results = _extract_tracking_ids(text, "matkahuolto")
        assert len(results) == 1
        assert results[0] == ("MH12345678", "matkahuolto")

    def test_no_duplicates(self):
        """Same tracking ID mentioned multiple times is returned once."""
        text = "JJFI12345678901 and again JJFI12345678901"
        results = _extract_tracking_ids(text, "posti")
        assert len(results) == 1

    def test_parse_full_email(self):
        """Parse a complete email message."""
        msg = _make_message(
            subject="Pakettisi on matkalla",
            sender="noreply@posti.fi",
            body="Seurantakoodisi on JJFI60773420139193970. Hyvää päivää!",
        )
        discovered = parse_email(msg)
        assert len(discovered) == 1
        assert discovered[0].tracking_id == "JJFI60773420139193970"
        assert discovered[0].vendor == "posti"
        assert discovered[0].source_sender == "noreply@posti.fi"

    def test_parse_email_no_tracking_id(self):
        """Email with no tracking ID returns empty list."""
        msg = _make_message(
            subject="Newsletter",
            sender="news@example.com",
            body="This is just a newsletter with no tracking info.",
        )
        assert parse_email(msg) == []

    def test_unknown_sender_tries_all_patterns(self):
        """Unknown sender tries Posti and Matkahuolto patterns."""
        msg = _make_message(
            subject="Order shipped",
            sender="shop@example.com",
            body="Track at JJFI99887766554",
        )
        discovered = parse_email(msg)
        assert len(discovered) == 1
        assert discovered[0].vendor == "posti"


# -- Email Service tests ---


def _make_settings(
    email_enabled: bool = False,
    email_host: str = "",
    email_port: int = 993,
    email_username: str = "",
    email_password: str = "",
    email_folder: str = "INBOX",
    email_auto_add: bool = False,
    email_poll_interval: int = 30,
    **kwargs,
) -> Settings:
    """Create a Settings instance with email fields overridden via env vars."""
    import os

    env = {
        "PAKETTI_EMAIL_ENABLED": str(email_enabled).lower(),
        "PAKETTI_EMAIL_HOST": email_host,
        "PAKETTI_EMAIL_PORT": str(email_port),
        "PAKETTI_EMAIL_USERNAME": email_username,
        "PAKETTI_EMAIL_PASSWORD": email_password,
        "PAKETTI_EMAIL_FOLDER": email_folder,
        "PAKETTI_EMAIL_AUTO_ADD": str(email_auto_add).lower(),
        "PAKETTI_EMAIL_POLL_INTERVAL": str(email_poll_interval),
        "PAKETTI_DATA_DIR": kwargs.get("data_dir", "/tmp"),
    }
    with patch.dict(os.environ, env, clear=False):
        return Settings()


@pytest.fixture
async def db(tmp_path):
    """Create a test database."""
    db_path = str(tmp_path / "test.db")
    database = Database(db_path)
    await database.initialize()
    yield database
    await database.close()


@pytest.mark.asyncio
async def test_email_service_disabled(db):
    """Service does nothing when email is disabled."""
    settings = _make_settings(email_enabled=False)
    service = EmailService(db, settings=settings)
    count = await service.poll_now()
    assert count == 0


@pytest.mark.asyncio
async def test_email_service_disabled_no_host(db):
    """Service does nothing when host is empty even if enabled."""
    settings = _make_settings(email_enabled=True, email_host="")
    service = EmailService(db, settings=settings)
    count = await service.poll_now()
    assert count == 0


@pytest.mark.asyncio
async def test_email_service_discovers_package(db):
    """Service discovers packages from email."""
    settings = _make_settings(
        email_enabled=True,
        email_host="imap.test.com",
        email_port=993,
        email_username="test@test.com",
        email_password="pass",
        email_folder="INBOX",
        email_auto_add=False,
    )

    mock_msg = _make_message(
        subject="Package shipped",
        sender="noreply@posti.fi",
        body="Tracking: JJFI12345678901",
    )

    with patch("app.services.email_service.EmailClient") as MockClient:
        instance = AsyncMock()
        instance.connect = AsyncMock()
        instance.disconnect = AsyncMock()
        instance.search_recent = AsyncMock(return_value=["1"])
        instance.fetch_messages = AsyncMock(return_value=[mock_msg])
        MockClient.return_value = instance

        service = EmailService(db, settings=settings)
        count = await service.poll_now()

    assert count == 1

    # Check it's in discovered list
    pkg_repo = PackageRepository(db)
    discovered = await pkg_repo.get_discovered()
    assert len(discovered) == 1
    assert discovered[0]["tracking_id"] == "JJFI12345678901"


@pytest.mark.asyncio
async def test_email_service_auto_add(db):
    """Service auto-adds when configured."""
    settings = _make_settings(
        email_enabled=True,
        email_host="imap.test.com",
        email_port=993,
        email_username="test@test.com",
        email_password="pass",
        email_folder="INBOX",
        email_auto_add=True,
    )

    mock_msg = _make_message(
        subject="Shipped",
        sender="noreply@posti.fi",
        body="Code: JJFI99887766554",
    )

    with patch("app.services.email_service.EmailClient") as MockClient:
        instance = AsyncMock()
        instance.connect = AsyncMock()
        instance.disconnect = AsyncMock()
        instance.search_recent = AsyncMock(return_value=["1"])
        instance.fetch_messages = AsyncMock(return_value=[mock_msg])
        MockClient.return_value = instance

        service = EmailService(db, settings=settings)
        count = await service.poll_now()

    assert count == 1

    # Should be in tracked packages, not discovered
    pkg_repo = PackageRepository(db)
    pkg = await pkg_repo.get_by_id("JJFI99887766554")
    assert pkg is not None
    assert pkg.vendor == "posti"

    discovered = await pkg_repo.get_discovered()
    assert len(discovered) == 0


@pytest.mark.asyncio
async def test_email_service_deduplication(db):
    """Service doesn't re-discover already tracked packages."""
    # Pre-add a package
    pkg_repo = PackageRepository(db)
    from app.db.models import PackageRow

    await pkg_repo.create(PackageRow(tracking_id="JJFI11111111111", vendor="posti"))

    settings = _make_settings(
        email_enabled=True,
        email_host="imap.test.com",
        email_port=993,
        email_username="test",
        email_password="pass",
        email_folder="INBOX",
        email_auto_add=False,
    )

    mock_msg = _make_message(
        subject="Shipped",
        sender="noreply@posti.fi",
        body="Track: JJFI11111111111",
    )

    with patch("app.services.email_service.EmailClient") as MockClient:
        instance = AsyncMock()
        instance.connect = AsyncMock()
        instance.disconnect = AsyncMock()
        instance.search_recent = AsyncMock(return_value=["1"])
        instance.fetch_messages = AsyncMock(return_value=[mock_msg])
        MockClient.return_value = instance

        service = EmailService(db, settings=settings)
        count = await service.poll_now()

    # Should not add duplicate
    assert count == 0
