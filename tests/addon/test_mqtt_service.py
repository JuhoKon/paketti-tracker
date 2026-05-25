"""Tests for MQTT service."""

from __future__ import annotations

import json
import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db.models import PackageRow
from app.services.mqtt_service import (
    MqttService,
    MqttCredentials,
    fetch_mqtt_credentials,
    _AVAILABILITY_TOPIC,
    _DISCOVERY_TOPIC,
    _STATE_TOPIC,
    _ATTRIBUTES_TOPIC,
    _FALLBACK_HOST,
    _FALLBACK_PORT,
)


@pytest.fixture
def mqtt_service():
    """Create an MQTT service for testing."""
    service = MqttService()
    return service


@pytest.fixture
def connected_service(mqtt_service):
    """Create a connected MQTT service with mocked client."""
    mqtt_service._connected = True
    mqtt_service._client = AsyncMock()
    return mqtt_service


@pytest.fixture
def sample_package():
    """Create a sample package for testing."""
    return PackageRow(
        tracking_id="JJFI12345678",
        vendor="posti",
        name="Test Package",
        status="in_transit",
        delivered=False,
        last_updated=datetime(2026, 5, 22, 10, 0),
        tracking_url="https://www.posti.fi/fi/seuranta#/lahetys/JJFI12345678",
        last_location="Helsinki",
        last_event_time=datetime(2026, 5, 22, 9, 0),
    )


# -- Credential fetching tests ---


@pytest.mark.asyncio
async def test_fetch_credentials_success():
    """Test successful credential fetch from Supervisor API."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = AsyncMock(return_value={
        "result": "ok",
        "data": {
            "host": "core-mosquitto",
            "port": 1883,
            "username": "homeassistant",
            "password": "secret123",
        },
    })
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    mock_session = AsyncMock()
    mock_session.get = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test-token"}):
        with patch("aiohttp.ClientSession", return_value=mock_session):
            creds = await fetch_mqtt_credentials()

    assert creds.host == "core-mosquitto"
    assert creds.port == 1883
    assert creds.username == "homeassistant"
    assert creds.password == "secret123"


@pytest.mark.asyncio
async def test_fetch_credentials_no_token():
    """Test fallback when SUPERVISOR_TOKEN is not set."""
    with patch.dict(os.environ, {}, clear=True):
        # Remove SUPERVISOR_TOKEN if present
        os.environ.pop("SUPERVISOR_TOKEN", None)
        creds = await fetch_mqtt_credentials()

    assert creds.host == _FALLBACK_HOST
    assert creds.port == _FALLBACK_PORT
    assert creds.username == ""
    assert creds.password == ""


@pytest.mark.asyncio
async def test_fetch_credentials_api_failure():
    """Test fallback when Supervisor API fails."""
    mock_session = AsyncMock()
    mock_session.get = MagicMock(side_effect=Exception("Connection refused"))
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "test-token"}):
        with patch("aiohttp.ClientSession", return_value=mock_session):
            creds = await fetch_mqtt_credentials()

    assert creds.host == _FALLBACK_HOST
    assert creds.port == _FALLBACK_PORT
    assert creds.username == ""
    assert creds.password == ""


# -- Discovery tests ---


@pytest.mark.asyncio
async def test_publish_package_discovery(connected_service, sample_package):
    """Test that discovery config is published."""
    await connected_service.publish_package(sample_package)

    calls = connected_service._client.publish.call_args_list

    # Should have 3 publishes: discovery, state, attributes
    assert len(calls) == 3

    # Check discovery topic
    discovery_call = calls[0]
    assert "homeassistant/sensor/paketti_tracker_jjfi12345678/config" == discovery_call.args[0]

    # Parse discovery payload
    payload = json.loads(discovery_call.args[1])
    assert payload["name"] == "Test Package"
    assert payload["unique_id"] == "paketti_tracker_jjfi12345678"
    assert payload["state_topic"] == "paketti_tracker/jjfi12345678/state"
    assert payload["device"]["identifiers"] == ["paketti_tracker"]
    assert payload["availability_topic"] == _AVAILABILITY_TOPIC


@pytest.mark.asyncio
async def test_publish_package_state(connected_service, sample_package):
    """Test that state is published."""
    await connected_service.publish_package(sample_package)

    calls = connected_service._client.publish.call_args_list
    state_call = calls[1]
    assert state_call.args[0] == "paketti_tracker/jjfi12345678/state"
    assert state_call.args[1] == "in_transit"


@pytest.mark.asyncio
async def test_publish_package_attributes(connected_service, sample_package):
    """Test that attributes are published."""
    await connected_service.publish_package(sample_package)

    calls = connected_service._client.publish.call_args_list
    attrs_call = calls[2]
    assert attrs_call.args[0] == "paketti_tracker/jjfi12345678/attributes"

    attrs = json.loads(attrs_call.args[1])
    assert attrs["vendor"] == "posti"
    assert attrs["name"] == "Test Package"
    assert attrs["delivered"] is False
    assert attrs["last_location"] == "Helsinki"
    assert attrs["tracking_url"] == "https://www.posti.fi/fi/seuranta#/lahetys/JJFI12345678"


# -- Removal tests ---


@pytest.mark.asyncio
async def test_remove_package(connected_service, sample_package):
    """Test removing a package publishes empty config."""
    # First publish the package
    await connected_service.publish_package(sample_package)
    connected_service._client.publish.reset_mock()

    # Remove it
    await connected_service.remove_package("JJFI12345678")

    # Should publish empty payload to discovery topic
    connected_service._client.publish.assert_called_once_with(
        "homeassistant/sensor/paketti_tracker_jjfi12345678/config",
        "",
        retain=True,
    )

    # Should be removed from cache
    assert "JJFI12345678" not in connected_service._packages_cache


# -- Availability tests ---


@pytest.mark.asyncio
async def test_republish_all(connected_service, sample_package):
    """Test republishing all packages."""
    # Populate cache
    connected_service._packages_cache["JJFI12345678"] = sample_package

    connected_service._client.publish.reset_mock()
    await connected_service.republish_all()

    # Should publish availability + package (discovery + state + attrs)
    calls = connected_service._client.publish.call_args_list
    assert len(calls) >= 4  # 1 availability + 3 for the package

    # First call should be availability
    assert calls[0].args[0] == _AVAILABILITY_TOPIC
    assert calls[0].args[1] == "online"


# -- Disconnected behavior ---


@pytest.mark.asyncio
async def test_publish_when_disconnected(mqtt_service, sample_package):
    """Test that packages are cached when disconnected."""
    await mqtt_service.publish_package(sample_package)

    # Should be cached
    assert "JJFI12345678" in mqtt_service._packages_cache
    assert mqtt_service._packages_cache["JJFI12345678"] == sample_package


@pytest.mark.asyncio
async def test_uses_tracking_id_as_name_fallback(connected_service):
    """Test that tracking_id is used when name is empty."""
    package = PackageRow(
        tracking_id="NONAME123",
        vendor="posti",
        name="",
        status="unknown",
    )
    await connected_service.publish_package(package)

    calls = connected_service._client.publish.call_args_list
    discovery_payload = json.loads(calls[0].args[1])
    assert discovery_payload["name"] == "NONAME123"


@pytest.mark.asyncio
async def test_delivered_icon(connected_service):
    """Test that delivered packages get check icon."""
    package = PackageRow(
        tracking_id="DONE1",
        vendor="posti",
        name="Done",
        status="delivered",
        delivered=True,
    )
    await connected_service.publish_package(package)

    calls = connected_service._client.publish.call_args_list
    discovery_payload = json.loads(calls[0].args[1])
    assert "check" in discovery_payload["icon"]
