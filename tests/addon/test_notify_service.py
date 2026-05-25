"""Tests for HA notify service."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.database import Database
from app.db.settings_repository import SettingsRepository
from app.services.notification_checker import NotificationEvent
from app.services.notify_service import NotifyService


@pytest.fixture
async def db(tmp_path):
    """Create a test database."""
    db_path = str(tmp_path / "test.db")
    database = Database(db_path)
    await database.initialize()
    yield database
    await database.close()


@pytest.fixture
def sample_event():
    """Create a sample notification event."""
    return NotificationEvent(
        tracking_id="JJFI12345678",
        package_name="Test Package",
        vendor="posti",
        event_type="delivered",
        old_status="in_transit",
        new_status="delivered",
        message="Package 'Test Package' has been delivered!",
    )


@pytest.mark.asyncio
async def test_send_disabled(db, sample_event):
    """Test no notifications sent when disabled."""
    settings_repo = SettingsRepository(db)
    await settings_repo.set_json("notifications", {
        "enabled": False,
        "devices": ["phone"],
        "triggers": [{"event_type": "delivered", "enabled": True}],
    })

    service = NotifyService(db, supervisor_token="fake-token")
    service._session = AsyncMock()

    await service.send_notifications([sample_event])

    # Should not have made any HTTP calls
    service._session.post.assert_not_called()


@pytest.mark.asyncio
async def test_send_no_devices(db, sample_event):
    """Test no notifications when no devices configured."""
    settings_repo = SettingsRepository(db)
    await settings_repo.set_json("notifications", {
        "enabled": True,
        "devices": [],
        "triggers": [{"event_type": "delivered", "enabled": True}],
    })

    service = NotifyService(db, supervisor_token="fake-token")
    service._session = AsyncMock()

    await service.send_notifications([sample_event])
    service._session.post.assert_not_called()


@pytest.mark.asyncio
async def test_send_trigger_disabled(db, sample_event):
    """Test no notification when trigger is disabled."""
    settings_repo = SettingsRepository(db)
    await settings_repo.set_json("notifications", {
        "enabled": True,
        "devices": ["phone"],
        "triggers": [{"event_type": "delivered", "enabled": False}],
    })

    service = NotifyService(db, supervisor_token="fake-token")
    service._session = AsyncMock()

    await service.send_notifications([sample_event])
    service._session.post.assert_not_called()


@pytest.mark.asyncio
async def test_send_success(db, sample_event):
    """Test successful notification delivery."""
    settings_repo = SettingsRepository(db)
    await settings_repo.set_json("notifications", {
        "enabled": True,
        "devices": ["phone"],
        "triggers": [{"event_type": "delivered", "enabled": True}],
    })

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    service = NotifyService(db, supervisor_token="fake-token", ha_api_url="http://test/api")
    service._session = MagicMock()
    service._session.post = MagicMock(return_value=mock_response)

    await service.send_notifications([sample_event])

    # Should have called post
    service._session.post.assert_called_once()
    call_args = service._session.post.call_args
    assert "notify/mobile_app_phone" in call_args.args[0]
    payload = call_args.kwargs["json"]
    assert payload["message"] == "Package 'Test Package' has been delivered!"
    assert payload["title"] == "Paketti Tracker"


@pytest.mark.asyncio
async def test_send_multiple_devices(db, sample_event):
    """Test notification sent to multiple devices."""
    settings_repo = SettingsRepository(db)
    await settings_repo.set_json("notifications", {
        "enabled": True,
        "devices": ["phone", "tablet"],
        "triggers": [{"event_type": "delivered", "enabled": True}],
    })

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    service = NotifyService(db, supervisor_token="fake-token", ha_api_url="http://test/api")
    service._session = MagicMock()
    service._session.post = MagicMock(return_value=mock_response)

    await service.send_notifications([sample_event])

    # Should have called post twice (once per device)
    assert service._session.post.call_count == 2


@pytest.mark.asyncio
async def test_send_empty_events(db):
    """Test no action on empty events list."""
    service = NotifyService(db, supervisor_token="fake-token")
    service._session = AsyncMock()

    await service.send_notifications([])
    service._session.post.assert_not_called()
