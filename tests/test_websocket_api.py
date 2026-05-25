"""Tests for the WebSocket API."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.paketti_tracker.const import (
    CONF_NAME,
    CONF_PACKAGES,
    CONF_POLL_INTERVAL,
    CONF_TRACKING_ID,
    CONF_VENDOR,
    DEFAULT_POLL_INTERVAL_MINUTES,
    DOMAIN,
    STATUS_IN_TRANSIT,
    VENDOR_POSTI,
    get_tracking_url,
)
from custom_components.paketti_tracker.models import TrackingEvent, TrackingResult
from custom_components.paketti_tracker.websocket_api import (
    ws_add_package,
    ws_edit_package,
    ws_get_settings,
    ws_packages,
    ws_refresh,
    ws_remove_package,
    ws_update_settings,
)

# The @websocket_api.async_response decorator wraps async handlers into sync
# schedulers. Access the original async function via __wrapped__ for testing.
_ws_packages = ws_packages.__wrapped__
_ws_add_package = ws_add_package.__wrapped__
_ws_edit_package = ws_edit_package.__wrapped__
_ws_remove_package = ws_remove_package.__wrapped__
_ws_refresh = ws_refresh.__wrapped__
_ws_get_settings = ws_get_settings.__wrapped__
_ws_update_settings = ws_update_settings.__wrapped__


def _make_result(
    tracking_id: str = "JJFI12345",
    status: str = STATUS_IN_TRANSIT,
    delivered: bool = False,
) -> TrackingResult:
    """Create a minimal TrackingResult for testing."""
    return TrackingResult(
        tracking_id=tracking_id,
        vendor=VENDOR_POSTI,
        status=status,
        delivered=delivered,
        events=[
            TrackingEvent(
                timestamp=datetime(2026, 5, 22, 10, 0, 0, tzinfo=UTC),
                description="In transit",
                location="HELSINKI",
            )
        ],
        last_location="HELSINKI",
        last_event_time=datetime(2026, 5, 22, 10, 0, 0, tzinfo=UTC),
    )


def _make_hass(
    packages: list[dict] | None = None,
    coordinator_data: dict[str, TrackingResult] | None = None,
    poll_interval: int | None = None,
) -> tuple[MagicMock, MagicMock, MagicMock]:
    """Create mock hass, connection, and entry for WS tests."""
    if packages is None:
        packages = [
            {CONF_TRACKING_ID: "JJFI12345", CONF_VENDOR: VENDOR_POSTI, CONF_NAME: "My Package"}
        ]

    entry = MagicMock()
    options = {CONF_PACKAGES: packages}
    if poll_interval is not None:
        options[CONF_POLL_INTERVAL] = poll_interval
    entry.options = options
    entry.entry_id = "test_entry"

    coordinator = MagicMock()
    coordinator.data = coordinator_data or {}
    coordinator.async_request_refresh = AsyncMock()
    coordinator.async_refresh = AsyncMock()

    hass = MagicMock()
    hass.data = {DOMAIN: {"test_entry": coordinator}}
    hass.config_entries = MagicMock()
    hass.config_entries.async_entries = MagicMock(return_value=[entry])
    hass.config_entries.async_update_entry = MagicMock()

    connection = MagicMock()
    connection.send_result = MagicMock()
    connection.send_error = MagicMock()

    return hass, connection, entry


# --- ws_packages ---


@pytest.mark.asyncio
async def test_packages_returns_all():
    """Test that packages command returns all configured packages."""
    result = _make_result("JJFI12345")
    hass, connection, entry = _make_hass(coordinator_data={"JJFI12345": result})

    msg = {"id": 1, "type": "paketti_tracker/packages"}
    await _ws_packages(hass, connection, msg)

    connection.send_result.assert_called_once()
    call_args = connection.send_result.call_args[0]
    assert call_args[0] == 1
    packages = call_args[1]["packages"]
    assert len(packages) == 1
    assert packages[0]["tracking_id"] == "JJFI12345"
    assert packages[0]["name"] == "My Package"
    assert packages[0]["status"] == STATUS_IN_TRANSIT
    assert len(packages[0]["events"]) == 1


@pytest.mark.asyncio
async def test_packages_no_data_yet():
    """Test that packages command returns placeholder when no data fetched."""
    hass, connection, entry = _make_hass(coordinator_data={})

    msg = {"id": 1, "type": "paketti_tracker/packages"}
    await _ws_packages(hass, connection, msg)

    call_args = connection.send_result.call_args[0]
    packages = call_args[1]["packages"]
    assert len(packages) == 1
    assert packages[0]["status"] == "unknown"
    assert packages[0]["events"] == []


@pytest.mark.asyncio
async def test_packages_not_configured():
    """Test error when integration not configured."""
    hass = MagicMock()
    hass.data = {}
    connection = MagicMock()

    msg = {"id": 1, "type": "paketti_tracker/packages"}
    await _ws_packages(hass, connection, msg)

    connection.send_error.assert_called_once_with(1, "not_configured", "Integration not configured")


# --- ws_add_package ---


@pytest.mark.asyncio
async def test_add_package_success():
    """Test adding a new package."""
    hass, connection, entry = _make_hass(packages=[])

    msg = {
        "id": 2,
        "type": "paketti_tracker/add_package",
        "tracking_id": "JJFI99999",
        "vendor": VENDOR_POSTI,
        "name": "New Package",
    }
    await _ws_add_package(hass, connection, msg)

    connection.send_result.assert_called_once()
    call_args = connection.send_result.call_args[0]
    assert call_args[1]["success"] is True
    assert call_args[1]["tracking_id"] == "JJFI99999"

    # Verify config entry was updated.
    hass.config_entries.async_update_entry.assert_called_once()
    update_call = hass.config_entries.async_update_entry.call_args
    new_packages = update_call[1]["options"][CONF_PACKAGES]
    assert len(new_packages) == 1
    assert new_packages[0][CONF_TRACKING_ID] == "JJFI99999"


@pytest.mark.asyncio
async def test_add_package_duplicate():
    """Test that duplicate tracking ID returns error."""
    hass, connection, entry = _make_hass()

    msg = {
        "id": 2,
        "type": "paketti_tracker/add_package",
        "tracking_id": "jjfi12345",  # lowercase, should be uppercased
        "vendor": VENDOR_POSTI,
        "name": "",
    }
    await _ws_add_package(hass, connection, msg)

    connection.send_error.assert_called_once_with(2, "already_tracked", "Package is already being tracked")


@pytest.mark.asyncio
async def test_add_package_empty_id():
    """Test that empty tracking ID returns error."""
    hass, connection, entry = _make_hass(packages=[])

    msg = {
        "id": 2,
        "type": "paketti_tracker/add_package",
        "tracking_id": "  ",
        "vendor": VENDOR_POSTI,
        "name": "",
    }
    await _ws_add_package(hass, connection, msg)

    connection.send_error.assert_called_once_with(2, "invalid_input", "Tracking ID cannot be empty")


# --- ws_remove_package ---


@pytest.mark.asyncio
async def test_remove_package_success():
    """Test removing a package."""
    hass, connection, entry = _make_hass()

    # Mock entity registry.
    mock_registry = MagicMock()
    mock_registry.async_get_entity_id = MagicMock(return_value="sensor.paketti_tracker_jjfi12345")
    mock_registry.async_remove = MagicMock()

    with patch(
        "custom_components.paketti_tracker.websocket_api.async_get_entity_registry",
        return_value=mock_registry,
    ):
        msg = {
            "id": 3,
            "type": "paketti_tracker/remove_package",
            "tracking_id": "JJFI12345",
        }
        await _ws_remove_package(hass, connection, msg)

    connection.send_result.assert_called_once()
    call_args = connection.send_result.call_args[0]
    assert call_args[1]["success"] is True

    # Verify package removed from config.
    update_call = hass.config_entries.async_update_entry.call_args
    new_packages = update_call[1]["options"][CONF_PACKAGES]
    assert len(new_packages) == 0

    # Verify entity removed.
    mock_registry.async_remove.assert_called_once_with("sensor.paketti_tracker_jjfi12345")


@pytest.mark.asyncio
async def test_remove_package_not_found():
    """Test removing a non-existent package."""
    hass, connection, entry = _make_hass()

    msg = {
        "id": 3,
        "type": "paketti_tracker/remove_package",
        "tracking_id": "NONEXISTENT",
    }

    with patch(
        "custom_components.paketti_tracker.websocket_api.async_get_entity_registry",
        return_value=MagicMock(),
    ):
        await _ws_remove_package(hass, connection, msg)

    connection.send_error.assert_called_once_with(3, "not_found", "Package not found")


# --- ws_refresh ---


@pytest.mark.asyncio
async def test_refresh_success():
    """Test refresh triggers coordinator update."""
    result = _make_result("JJFI12345")
    hass, connection, entry = _make_hass(coordinator_data={"JJFI12345": result})

    # Mock async_refresh to simulate data update.
    coordinator = next(iter(hass.data[DOMAIN].values()))
    coordinator.async_refresh = AsyncMock()

    msg = {"id": 4, "type": "paketti_tracker/refresh"}
    await _ws_refresh(hass, connection, msg)

    coordinator.async_refresh.assert_called_once()
    connection.send_result.assert_called_once()
    call_args = connection.send_result.call_args[0]
    assert "packages" in call_args[1]


# --- ws_get_settings ---


@pytest.mark.asyncio
async def test_get_settings_default():
    """Test get_settings returns default poll interval."""
    hass, connection, entry = _make_hass()

    msg = {"id": 5, "type": "paketti_tracker/get_settings"}
    await _ws_get_settings(hass, connection, msg)

    connection.send_result.assert_called_once()
    call_args = connection.send_result.call_args[0]
    assert call_args[1]["poll_interval_minutes"] == DEFAULT_POLL_INTERVAL_MINUTES


@pytest.mark.asyncio
async def test_get_settings_custom():
    """Test get_settings returns custom poll interval."""
    hass, connection, entry = _make_hass(poll_interval=30)

    msg = {"id": 5, "type": "paketti_tracker/get_settings"}
    await _ws_get_settings(hass, connection, msg)

    call_args = connection.send_result.call_args[0]
    assert call_args[1]["poll_interval_minutes"] == 30


# --- ws_update_settings ---


@pytest.mark.asyncio
async def test_update_settings():
    """Test update_settings changes poll interval."""
    hass, connection, entry = _make_hass()

    msg = {"id": 6, "type": "paketti_tracker/update_settings", "poll_interval_minutes": 15}
    await _ws_update_settings(hass, connection, msg)

    connection.send_result.assert_called_once()
    call_args = connection.send_result.call_args[0]
    assert call_args[1]["poll_interval_minutes"] == 15

    # Verify config entry updated.
    update_call = hass.config_entries.async_update_entry.call_args
    assert update_call[1]["options"][CONF_POLL_INTERVAL] == 15

    # Verify coordinator interval updated.
    coordinator = next(iter(hass.data[DOMAIN].values()))
    assert coordinator.update_interval == timedelta(minutes=15)


# --- ws_edit_package ---


@pytest.mark.asyncio
async def test_edit_package_name():
    """Test editing a package name."""
    packages = [
        {CONF_TRACKING_ID: "JJFI12345", CONF_VENDOR: VENDOR_POSTI, CONF_NAME: "Old Name"}
    ]
    hass, connection, entry = _make_hass(packages=packages)

    msg = {"id": 7, "type": "paketti_tracker/edit_package", "tracking_id": "JJFI12345", "name": "New Name"}
    await _ws_edit_package(hass, connection, msg)

    connection.send_result.assert_called_once()
    call_args = connection.send_result.call_args[0]
    assert call_args[1]["success"] is True

    # Verify config entry updated with new name.
    update_call = hass.config_entries.async_update_entry.call_args
    updated_packages = update_call[1]["options"][CONF_PACKAGES]
    assert updated_packages[0][CONF_NAME] == "New Name"


@pytest.mark.asyncio
async def test_edit_package_vendor():
    """Test editing a package vendor triggers refresh."""
    packages = [
        {CONF_TRACKING_ID: "JJFI12345", CONF_VENDOR: VENDOR_POSTI, CONF_NAME: "My Package"}
    ]
    hass, connection, entry = _make_hass(packages=packages)

    msg = {"id": 7, "type": "paketti_tracker/edit_package", "tracking_id": "JJFI12345", "vendor": "postnord"}
    await _ws_edit_package(hass, connection, msg)

    connection.send_result.assert_called_once()
    # Verify vendor updated.
    update_call = hass.config_entries.async_update_entry.call_args
    updated_packages = update_call[1]["options"][CONF_PACKAGES]
    assert updated_packages[0][CONF_VENDOR] == "postnord"

    # Verify coordinator refresh triggered.
    coordinator = next(iter(hass.data[DOMAIN].values()))
    coordinator.async_request_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_edit_package_not_found():
    """Test editing a non-existent package returns error."""
    hass, connection, entry = _make_hass()

    msg = {"id": 7, "type": "paketti_tracker/edit_package", "tracking_id": "NOTEXIST", "name": "X"}
    await _ws_edit_package(hass, connection, msg)

    connection.send_error.assert_called_once()
    error_args = connection.send_error.call_args[0]
    assert error_args[1] == "not_found"


# --- last_updated and tracking_url in ws_packages ---


@pytest.mark.asyncio
async def test_packages_includes_last_updated_and_tracking_url():
    """Test that packages response includes last_updated and tracking_url."""
    result = _make_result("JJFI12345")
    result.last_updated = datetime(2026, 5, 25, 12, 0, 0, tzinfo=UTC)
    hass, connection, entry = _make_hass(coordinator_data={"JJFI12345": result})

    msg = {"id": 1, "type": "paketti_tracker/packages"}
    await _ws_packages(hass, connection, msg)

    call_args = connection.send_result.call_args[0]
    pkg = call_args[1]["packages"][0]
    assert pkg["last_updated"] == "2026-05-25T12:00:00+00:00"
    assert pkg["tracking_url"] == "https://www.posti.fi/fi/seuranta#/lahetys/JJFI12345"


@pytest.mark.asyncio
async def test_packages_no_data_includes_tracking_url():
    """Test packages with no tracking data still include tracking_url."""
    hass, connection, entry = _make_hass(coordinator_data={})

    msg = {"id": 1, "type": "paketti_tracker/packages"}
    await _ws_packages(hass, connection, msg)

    call_args = connection.send_result.call_args[0]
    pkg = call_args[1]["packages"][0]
    assert pkg["last_updated"] is None
    assert pkg["tracking_url"] == "https://www.posti.fi/fi/seuranta#/lahetys/JJFI12345"


# --- get_tracking_url ---


def test_get_tracking_url_posti():
    """Test Posti tracking URL."""
    assert get_tracking_url("posti", "JJFI12345") == "https://www.posti.fi/fi/seuranta#/lahetys/JJFI12345"


def test_get_tracking_url_postnord():
    """Test Postnord tracking URL."""
    assert get_tracking_url("postnord", "ABC123") == "https://tracking.postnord.com/fi/?id=ABC123"


def test_get_tracking_url_matkahuolto():
    """Test Matkahuolto tracking URL."""
    assert get_tracking_url("matkahuolto", "MH999") == "https://www.matkahuolto.fi/seuranta/tilaus/MH999"


def test_get_tracking_url_unknown_vendor():
    """Test unknown vendor returns None."""
    assert get_tracking_url("unknown_carrier", "XYZ") is None
