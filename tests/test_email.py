"""Tests for email parsing and email WS commands."""

from __future__ import annotations

from email.message import Message
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.paketti_tracker.const import (
    CONF_DISCOVERED_PACKAGES,
    CONF_EMAIL,
    CONF_EMAIL_ENABLED,
    CONF_EMAIL_IMAP_PORT,
    CONF_EMAIL_IMAP_SERVER,
    CONF_EMAIL_PASSWORD,
    CONF_EMAIL_USERNAME,
    CONF_NAME,
    CONF_PACKAGES,
    CONF_TRACKING_ID,
    DOMAIN,
)
from custom_components.paketti_tracker.email_coordinator import get_email_config
from custom_components.paketti_tracker.email_parser import parse_email
from custom_components.paketti_tracker.websocket_api import (
    ws_confirm_package,
    ws_discovered_packages,
    ws_dismiss_package,
    ws_get_email_config,
    ws_test_email_connection,
    ws_update_email_config,
)

_ws_get_email_config = ws_get_email_config.__wrapped__
_ws_update_email_config = ws_update_email_config.__wrapped__
_ws_test_email_connection = ws_test_email_connection.__wrapped__
_ws_discovered_packages = ws_discovered_packages.__wrapped__
_ws_confirm_package = ws_confirm_package.__wrapped__
_ws_dismiss_package = ws_dismiss_package.__wrapped__


def _make_email(subject: str, sender: str, body: str) -> Message:
    """Create a simple email message for testing."""
    msg = Message()
    msg["Subject"] = subject
    msg["From"] = sender
    msg.set_payload(body.encode("utf-8"))
    msg.set_type("text/plain")
    msg.set_charset("utf-8")
    return msg


def _make_hass_email(
    email_config: dict | None = None,
    discovered: list | None = None,
    packages: list | None = None,
):
    """Create mock hass with email config."""
    entry = MagicMock()
    options: dict = {CONF_PACKAGES: packages or []}
    if email_config is not None:
        options[CONF_EMAIL] = email_config
    if discovered is not None:
        options[CONF_DISCOVERED_PACKAGES] = discovered
    entry.options = options
    entry.entry_id = "test_entry"

    coordinator = MagicMock()
    coordinator.data = {}
    coordinator.async_request_refresh = AsyncMock()

    hass = MagicMock()
    hass.data = {DOMAIN: {"test_entry": coordinator}}
    hass.config_entries = MagicMock()
    hass.config_entries.async_entries = MagicMock(return_value=[entry])
    hass.config_entries.async_update_entry = MagicMock()

    connection = MagicMock()
    connection.send_result = MagicMock()
    connection.send_error = MagicMock()

    return hass, connection, entry


# --- email_parser tests ---


def test_parse_posti_tracking_from_subject():
    """Test extracting Posti tracking ID from email subject."""
    msg = _make_email(
        subject="Lähetyksesi JJFI123456789 on matkalla",
        sender="noreply@posti.fi",
        body="Tracking details...",
    )
    results = parse_email(msg)
    assert len(results) == 1
    assert results[0].tracking_id == "JJFI123456789"
    assert results[0].vendor == "posti"


def test_parse_posti_tracking_from_body():
    """Test extracting Posti tracking ID from email body."""
    msg = _make_email(
        subject="Pakettisi on saapunut",
        sender="noreply@posti.fi",
        body="Seuraa lähetystäsi: JJFI987654321. Kiitos!",
    )
    results = parse_email(msg)
    assert len(results) == 1
    assert results[0].tracking_id == "JJFI987654321"


def test_parse_posti_international_format():
    """Test extracting international Posti format (XX999999999FI)."""
    msg = _make_email(
        subject="Your shipment",
        sender="shop@posti.fi",
        body="Tracking code: RA123456789FI",
    )
    results = parse_email(msg)
    assert len(results) == 1
    assert results[0].tracking_id == "RA123456789FI"
    assert results[0].vendor == "posti"


def test_parse_matkahuolto_tracking():
    """Test extracting Matkahuolto tracking ID."""
    msg = _make_email(
        subject="Tilausvahvistus",
        sender="info@matkahuolto.fi",
        body="Seurantanumero: MH12345678",
    )
    results = parse_email(msg)
    assert len(results) == 1
    assert results[0].tracking_id == "MH12345678"
    assert results[0].vendor == "matkahuolto"


def test_parse_no_tracking():
    """Test email with no tracking IDs returns empty."""
    msg = _make_email(
        subject="Newsletter",
        sender="news@example.com",
        body="No tracking info here.",
    )
    results = parse_email(msg)
    assert len(results) == 0


def test_parse_multiple_tracking_ids():
    """Test multiple tracking IDs in one email."""
    msg = _make_email(
        subject="Your packages",
        sender="orders@posti.fi",
        body="Package 1: JJFI111111111\nPackage 2: JJFI222222222",
    )
    results = parse_email(msg)
    assert len(results) == 2
    ids = {r.tracking_id for r in results}
    assert ids == {"JJFI111111111", "JJFI222222222"}


def test_parse_deduplicates():
    """Test same tracking ID appearing twice is deduplicated."""
    msg = _make_email(
        subject="JJFI111111111",
        sender="noreply@posti.fi",
        body="Your package JJFI111111111 is on its way.",
    )
    results = parse_email(msg)
    assert len(results) == 1


# --- get_email_config ---


def test_get_email_config_defaults():
    """Test email config defaults."""
    config = get_email_config({})
    assert config["enabled"] is False
    assert config["imap_server"] == ""
    assert config["imap_port"] == 993
    assert config["folder"] == "INBOX"
    assert config["auto_add"] is False
    assert config["search_days"] == 7


# --- ws_get_email_config ---


@pytest.mark.asyncio
async def test_ws_get_email_config_defaults():
    """Test get_email_config WS returns defaults."""
    hass, connection, entry = _make_hass_email()

    msg = {"id": 20, "type": "paketti_tracker/get_email_config"}
    await _ws_get_email_config(hass, connection, msg)

    connection.send_result.assert_called_once()
    result = connection.send_result.call_args[0][1]
    assert result["enabled"] is False
    assert result["password"] == ""  # Not exposed


@pytest.mark.asyncio
async def test_ws_get_email_config_hides_password():
    """Test get_email_config masks password."""
    hass, connection, entry = _make_hass_email(
        email_config={
            CONF_EMAIL_ENABLED: True,
            CONF_EMAIL_IMAP_SERVER: "imap.example.com",
            CONF_EMAIL_IMAP_PORT: 993,
            CONF_EMAIL_USERNAME: "user@example.com",
            CONF_EMAIL_PASSWORD: "secret123",
        }
    )

    msg = {"id": 20, "type": "paketti_tracker/get_email_config"}
    await _ws_get_email_config(hass, connection, msg)

    result = connection.send_result.call_args[0][1]
    assert result["password"] == "***"
    assert result["imap_server"] == "imap.example.com"


# --- ws_update_email_config ---


@pytest.mark.asyncio
async def test_ws_update_email_config():
    """Test update_email_config updates settings."""
    hass, connection, entry = _make_hass_email()

    msg = {
        "id": 21,
        "type": "paketti_tracker/update_email_config",
        "enabled": True,
        "imap_server": "imap.gmail.com",
        "imap_port": 993,
        "username": "user@gmail.com",
        "password": "app_password",
    }
    await _ws_update_email_config(hass, connection, msg)

    connection.send_result.assert_called_once()
    result = connection.send_result.call_args[0][1]
    assert result["enabled"] is True
    assert result["imap_server"] == "imap.gmail.com"
    assert result["password"] == "***"  # Masked in response


# --- ws_discovered_packages ---


@pytest.mark.asyncio
async def test_ws_discovered_packages_empty():
    """Test discovered_packages returns empty list."""
    hass, connection, entry = _make_hass_email()

    msg = {"id": 22, "type": "paketti_tracker/discovered_packages"}
    await _ws_discovered_packages(hass, connection, msg)

    result = connection.send_result.call_args[0][1]
    assert result["packages"] == []


@pytest.mark.asyncio
async def test_ws_discovered_packages_with_data():
    """Test discovered_packages returns discovered list."""
    discovered = [
        {
            "tracking_id": "JJFI999999999",
            "vendor": "posti",
            "source_subject": "Your package",
            "source_sender": "noreply@posti.fi",
            "discovered_at": "2026-05-25T12:00:00+00:00",
        }
    ]
    hass, connection, entry = _make_hass_email(discovered=discovered)

    msg = {"id": 22, "type": "paketti_tracker/discovered_packages"}
    await _ws_discovered_packages(hass, connection, msg)

    result = connection.send_result.call_args[0][1]
    assert len(result["packages"]) == 1
    assert result["packages"][0]["tracking_id"] == "JJFI999999999"


# --- ws_confirm_package ---


@pytest.mark.asyncio
async def test_ws_confirm_package():
    """Test confirming a discovered package moves it to tracked."""
    discovered = [
        {
            "tracking_id": "JJFI999999999",
            "vendor": "posti",
            "source_subject": "Your package",
            "source_sender": "noreply@posti.fi",
            "discovered_at": "2026-05-25T12:00:00+00:00",
        }
    ]
    hass, connection, entry = _make_hass_email(discovered=discovered)

    msg = {
        "id": 23,
        "type": "paketti_tracker/confirm_package",
        "tracking_id": "JJFI999999999",
        "name": "My New Package",
    }
    await _ws_confirm_package(hass, connection, msg)

    connection.send_result.assert_called_once()
    result = connection.send_result.call_args[0][1]
    assert result["success"] is True

    # Verify config entry updated.
    update_call = hass.config_entries.async_update_entry.call_args
    opts = update_call[1]["options"]
    assert len(opts[CONF_PACKAGES]) == 1
    assert opts[CONF_PACKAGES][0][CONF_TRACKING_ID] == "JJFI999999999"
    assert opts[CONF_PACKAGES][0][CONF_NAME] == "My New Package"
    assert opts[CONF_DISCOVERED_PACKAGES] == []


@pytest.mark.asyncio
async def test_ws_confirm_package_not_found():
    """Test confirming non-existent package returns error."""
    hass, connection, entry = _make_hass_email(discovered=[])

    msg = {
        "id": 23,
        "type": "paketti_tracker/confirm_package",
        "tracking_id": "NOTEXIST",
    }
    await _ws_confirm_package(hass, connection, msg)

    connection.send_error.assert_called_once()
    assert connection.send_error.call_args[0][1] == "not_found"


# --- ws_dismiss_package ---


@pytest.mark.asyncio
async def test_ws_dismiss_package():
    """Test dismissing a discovered package removes it."""
    discovered = [
        {
            "tracking_id": "JJFI999999999",
            "vendor": "posti",
            "source_subject": "Your package",
            "source_sender": "noreply@posti.fi",
            "discovered_at": "2026-05-25T12:00:00+00:00",
        }
    ]
    hass, connection, entry = _make_hass_email(discovered=discovered)

    msg = {"id": 24, "type": "paketti_tracker/dismiss_package", "tracking_id": "JJFI999999999"}
    await _ws_dismiss_package(hass, connection, msg)

    connection.send_result.assert_called_once()
    update_call = hass.config_entries.async_update_entry.call_args
    assert update_call[1]["options"][CONF_DISCOVERED_PACKAGES] == []


@pytest.mark.asyncio
async def test_ws_dismiss_package_not_found():
    """Test dismissing non-existent package returns error."""
    hass, connection, entry = _make_hass_email(discovered=[])

    msg = {"id": 24, "type": "paketti_tracker/dismiss_package", "tracking_id": "NOTEXIST"}
    await _ws_dismiss_package(hass, connection, msg)

    connection.send_error.assert_called_once()
    assert connection.send_error.call_args[0][1] == "not_found"
