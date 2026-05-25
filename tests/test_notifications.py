"""Tests for notification logic."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.paketti_tracker.const import (
    CONF_NOTIFICATIONS,
    CONF_NOTIFICATIONS_DEVICES,
    CONF_NOTIFICATIONS_ENABLED,
    CONF_NOTIFICATIONS_TRIGGERS,
    CONF_PACKAGES,
    DEFAULT_NOTIFICATION_TRIGGERS,
    DOMAIN,
    STATUS_DELIVERED,
    STATUS_EXCEPTION,
    STATUS_IN_TRANSIT,
    STATUS_PENDING,
    VENDOR_POSTI,
)
from custom_components.paketti_tracker.notifications import (
    async_check_and_notify,
    async_send_notification,
    get_notification_config,
)
from custom_components.paketti_tracker.websocket_api import (
    ws_get_notifications,
    ws_update_notifications,
)

_ws_get_notifications = ws_get_notifications.__wrapped__
_ws_update_notifications = ws_update_notifications.__wrapped__


# --- get_notification_config ---


def test_get_notification_config_defaults():
    """Test defaults when no notification config is set."""
    config = get_notification_config({})
    assert config[CONF_NOTIFICATIONS_ENABLED] is False
    assert config[CONF_NOTIFICATIONS_TRIGGERS] == DEFAULT_NOTIFICATION_TRIGGERS
    assert config[CONF_NOTIFICATIONS_DEVICES] == []


def test_get_notification_config_custom():
    """Test reading custom notification config."""
    options = {
        CONF_NOTIFICATIONS: {
            CONF_NOTIFICATIONS_ENABLED: True,
            CONF_NOTIFICATIONS_TRIGGERS: [STATUS_DELIVERED],
            CONF_NOTIFICATIONS_DEVICES: ["mobile_app_phone"],
        }
    }
    config = get_notification_config(options)
    assert config[CONF_NOTIFICATIONS_ENABLED] is True
    assert config[CONF_NOTIFICATIONS_TRIGGERS] == [STATUS_DELIVERED]
    assert config[CONF_NOTIFICATIONS_DEVICES] == ["mobile_app_phone"]


# --- async_check_and_notify ---


@pytest.mark.asyncio
async def test_check_and_notify_disabled():
    """Test no notification when disabled."""
    hass = MagicMock()
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()

    options = {CONF_NOTIFICATIONS: {CONF_NOTIFICATIONS_ENABLED: False}}
    await async_check_and_notify(
        hass, options, old_status=STATUS_PENDING, new_status=STATUS_IN_TRANSIT,
        package_name="Test", vendor=VENDOR_POSTI, event_description=None,
    )
    hass.services.async_call.assert_not_called()


@pytest.mark.asyncio
async def test_check_and_notify_no_old_status():
    """Test no notification on first poll (no old status)."""
    hass = MagicMock()
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()

    options = {
        CONF_NOTIFICATIONS: {
            CONF_NOTIFICATIONS_ENABLED: True,
            CONF_NOTIFICATIONS_TRIGGERS: DEFAULT_NOTIFICATION_TRIGGERS,
            CONF_NOTIFICATIONS_DEVICES: ["mobile_app_phone"],
        }
    }
    await async_check_and_notify(
        hass, options, old_status=None, new_status=STATUS_IN_TRANSIT,
        package_name="Test", vendor=VENDOR_POSTI, event_description=None,
    )
    hass.services.async_call.assert_not_called()


@pytest.mark.asyncio
async def test_check_and_notify_no_change():
    """Test no notification when status unchanged."""
    hass = MagicMock()
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()

    options = {
        CONF_NOTIFICATIONS: {
            CONF_NOTIFICATIONS_ENABLED: True,
            CONF_NOTIFICATIONS_TRIGGERS: DEFAULT_NOTIFICATION_TRIGGERS,
            CONF_NOTIFICATIONS_DEVICES: ["mobile_app_phone"],
        }
    }
    await async_check_and_notify(
        hass, options, old_status=STATUS_IN_TRANSIT, new_status=STATUS_IN_TRANSIT,
        package_name="Test", vendor=VENDOR_POSTI, event_description=None,
    )
    hass.services.async_call.assert_not_called()


@pytest.mark.asyncio
async def test_check_and_notify_trigger_not_in_list():
    """Test no notification when new status not in triggers."""
    hass = MagicMock()
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()

    options = {
        CONF_NOTIFICATIONS: {
            CONF_NOTIFICATIONS_ENABLED: True,
            CONF_NOTIFICATIONS_TRIGGERS: [STATUS_DELIVERED],  # Only delivered
            CONF_NOTIFICATIONS_DEVICES: ["mobile_app_phone"],
        }
    }
    await async_check_and_notify(
        hass, options, old_status=STATUS_PENDING, new_status=STATUS_IN_TRANSIT,
        package_name="Test", vendor=VENDOR_POSTI, event_description=None,
    )
    hass.services.async_call.assert_not_called()


@pytest.mark.asyncio
async def test_check_and_notify_sends():
    """Test notification sent on matching trigger."""
    hass = MagicMock()
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()

    options = {
        CONF_NOTIFICATIONS: {
            CONF_NOTIFICATIONS_ENABLED: True,
            CONF_NOTIFICATIONS_TRIGGERS: [STATUS_DELIVERED],
            CONF_NOTIFICATIONS_DEVICES: ["mobile_app_phone"],
        }
    }
    await async_check_and_notify(
        hass, options, old_status=STATUS_IN_TRANSIT, new_status=STATUS_DELIVERED,
        package_name="My Package", vendor=VENDOR_POSTI, event_description="Delivered to mailbox",
    )
    hass.services.async_call.assert_called_once()
    call_args = hass.services.async_call.call_args
    assert call_args[0][0] == "notify"
    assert call_args[0][1] == "mobile_app_phone"
    assert "My Package" in call_args[0][2]["title"]
    assert "Delivered" in call_args[0][2]["message"]
    assert "Delivered to mailbox" in call_args[0][2]["message"]


@pytest.mark.asyncio
async def test_check_and_notify_multiple_devices():
    """Test notification sent to multiple devices."""
    hass = MagicMock()
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()

    options = {
        CONF_NOTIFICATIONS: {
            CONF_NOTIFICATIONS_ENABLED: True,
            CONF_NOTIFICATIONS_TRIGGERS: [STATUS_IN_TRANSIT],
            CONF_NOTIFICATIONS_DEVICES: ["mobile_app_phone", "mobile_app_tablet"],
        }
    }
    await async_check_and_notify(
        hass, options, old_status=STATUS_PENDING, new_status=STATUS_IN_TRANSIT,
        package_name="Test", vendor=VENDOR_POSTI, event_description=None,
    )
    assert hass.services.async_call.call_count == 2


# --- async_send_notification ---


@pytest.mark.asyncio
async def test_send_notification_no_devices():
    """Test no service call when no devices."""
    hass = MagicMock()
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()

    await async_send_notification(
        hass, package_name="Test", vendor=VENDOR_POSTI,
        new_status=STATUS_DELIVERED, event_description=None, devices=[],
    )
    hass.services.async_call.assert_not_called()


# --- ws_get_notifications ---


def _make_hass_with_notifications(notifications_config: dict | None = None):
    """Create mock hass with notification config."""
    entry = MagicMock()
    options = {CONF_PACKAGES: []}
    if notifications_config is not None:
        options[CONF_NOTIFICATIONS] = notifications_config
    entry.options = options
    entry.entry_id = "test_entry"

    coordinator = MagicMock()
    coordinator.data = {}

    hass = MagicMock()
    hass.data = {DOMAIN: {"test_entry": coordinator}}
    hass.config_entries = MagicMock()
    hass.config_entries.async_entries = MagicMock(return_value=[entry])
    hass.config_entries.async_update_entry = MagicMock()

    connection = MagicMock()
    connection.send_result = MagicMock()
    connection.send_error = MagicMock()

    return hass, connection, entry


@pytest.mark.asyncio
async def test_ws_get_notifications_defaults():
    """Test get_notifications returns defaults."""
    hass, connection, entry = _make_hass_with_notifications()

    msg = {"id": 10, "type": "paketti_tracker/get_notifications"}
    await _ws_get_notifications(hass, connection, msg)

    connection.send_result.assert_called_once()
    result = connection.send_result.call_args[0][1]
    assert result[CONF_NOTIFICATIONS_ENABLED] is False
    assert result[CONF_NOTIFICATIONS_TRIGGERS] == DEFAULT_NOTIFICATION_TRIGGERS
    assert result[CONF_NOTIFICATIONS_DEVICES] == []


@pytest.mark.asyncio
async def test_ws_get_notifications_custom():
    """Test get_notifications returns custom config."""
    hass, connection, entry = _make_hass_with_notifications(
        {
            CONF_NOTIFICATIONS_ENABLED: True,
            CONF_NOTIFICATIONS_TRIGGERS: [STATUS_DELIVERED],
            CONF_NOTIFICATIONS_DEVICES: ["mobile_app_phone"],
        }
    )

    msg = {"id": 10, "type": "paketti_tracker/get_notifications"}
    await _ws_get_notifications(hass, connection, msg)

    result = connection.send_result.call_args[0][1]
    assert result[CONF_NOTIFICATIONS_ENABLED] is True
    assert result[CONF_NOTIFICATIONS_TRIGGERS] == [STATUS_DELIVERED]


@pytest.mark.asyncio
async def test_ws_update_notifications():
    """Test update_notifications updates config."""
    hass, connection, entry = _make_hass_with_notifications()

    msg = {
        "id": 11,
        "type": "paketti_tracker/update_notifications",
        "enabled": True,
        "triggers": [STATUS_DELIVERED, STATUS_EXCEPTION],
        "devices": ["mobile_app_phone"],
    }
    await _ws_update_notifications(hass, connection, msg)

    connection.send_result.assert_called_once()
    result = connection.send_result.call_args[0][1]
    assert result[CONF_NOTIFICATIONS_ENABLED] is True
    assert result[CONF_NOTIFICATIONS_TRIGGERS] == [STATUS_DELIVERED, STATUS_EXCEPTION]
    assert result[CONF_NOTIFICATIONS_DEVICES] == ["mobile_app_phone"]

    # Verify config entry was updated.
    update_call = hass.config_entries.async_update_entry.call_args
    assert CONF_NOTIFICATIONS in update_call[1]["options"]


@pytest.mark.asyncio
async def test_ws_update_notifications_partial():
    """Test update_notifications with partial fields merges with existing."""
    hass, connection, entry = _make_hass_with_notifications(
        {
            CONF_NOTIFICATIONS_ENABLED: True,
            CONF_NOTIFICATIONS_TRIGGERS: [STATUS_IN_TRANSIT, STATUS_DELIVERED],
            CONF_NOTIFICATIONS_DEVICES: ["mobile_app_phone"],
        }
    )

    # Only update enabled flag.
    msg = {
        "id": 11,
        "type": "paketti_tracker/update_notifications",
        "enabled": False,
    }
    await _ws_update_notifications(hass, connection, msg)

    result = connection.send_result.call_args[0][1]
    assert result[CONF_NOTIFICATIONS_ENABLED] is False
    # Other fields preserved.
    assert result[CONF_NOTIFICATIONS_TRIGGERS] == [STATUS_IN_TRANSIT, STATUS_DELIVERED]
    assert result[CONF_NOTIFICATIONS_DEVICES] == ["mobile_app_phone"]
