"""Tests for the database repository layer."""

from __future__ import annotations

from datetime import datetime

import pytest

from app.database import Database
from app.db.models import PackageRow, TrackingEventRow
from app.db.repository import PackageRepository
from app.db.settings_repository import SettingsRepository


@pytest.fixture
async def db(tmp_path):
    """Create an in-memory database for testing."""
    db_path = str(tmp_path / "test.db")
    database = Database(db_path)
    await database.initialize()
    yield database
    await database.close()


@pytest.fixture
async def repo(db):
    """Create a PackageRepository."""
    return PackageRepository(db)


@pytest.fixture
async def settings_repo(db):
    """Create a SettingsRepository."""
    return SettingsRepository(db)


# --- Package CRUD tests ---


@pytest.mark.asyncio
async def test_create_and_get_package(repo: PackageRepository):
    """Test creating and retrieving a package."""
    package = PackageRow(
        tracking_id="JJFI12345678",
        vendor="posti",
        name="Test Package",
        status="in_transit",
        tracking_url="https://www.posti.fi/fi/seuranta#/lahetys/JJFI12345678",
    )
    created = await repo.create(package)
    assert created.tracking_id == "JJFI12345678"

    retrieved = await repo.get_by_id("JJFI12345678")
    assert retrieved is not None
    assert retrieved.vendor == "posti"
    assert retrieved.name == "Test Package"
    assert retrieved.status == "in_transit"


@pytest.mark.asyncio
async def test_get_all_packages(repo: PackageRepository):
    """Test listing all packages."""
    await repo.create(PackageRow(tracking_id="PKG1", vendor="posti", name="First"))
    await repo.create(PackageRow(tracking_id="PKG2", vendor="postnord", name="Second"))

    packages = await repo.get_all()
    assert len(packages) == 2


@pytest.mark.asyncio
async def test_get_active_packages(repo: PackageRepository):
    """Test listing only non-delivered packages."""
    await repo.create(PackageRow(tracking_id="ACTIVE1", vendor="posti", delivered=False))
    await repo.create(PackageRow(tracking_id="DONE1", vendor="posti", delivered=True))

    active = await repo.get_active()
    assert len(active) == 1
    assert active[0].tracking_id == "ACTIVE1"


@pytest.mark.asyncio
async def test_update_package(repo: PackageRepository):
    """Test updating package fields."""
    await repo.create(PackageRow(tracking_id="UPD1", vendor="posti", name="Old Name"))

    updated = await repo.update("UPD1", name="New Name", status="delivered", delivered=True)
    assert updated is not None
    assert updated.name == "New Name"
    assert updated.status == "delivered"
    assert updated.delivered is True


@pytest.mark.asyncio
async def test_delete_package(repo: PackageRepository):
    """Test deleting a package."""
    await repo.create(PackageRow(tracking_id="DEL1", vendor="posti"))

    deleted = await repo.delete("DEL1")
    assert deleted is True

    retrieved = await repo.get_by_id("DEL1")
    assert retrieved is None


@pytest.mark.asyncio
async def test_delete_nonexistent(repo: PackageRepository):
    """Test deleting a package that doesn't exist."""
    deleted = await repo.delete("NONEXISTENT")
    assert deleted is False


# --- Tracking Events tests ---


@pytest.mark.asyncio
async def test_add_and_get_events(repo: PackageRepository):
    """Test adding and retrieving tracking events."""
    await repo.create(PackageRow(tracking_id="EVT1", vendor="posti"))

    events = [
        TrackingEventRow(
            tracking_id="EVT1",
            timestamp=datetime(2026, 5, 20, 10, 0),
            description="Shipment registered",
            location="Helsinki",
        ),
        TrackingEventRow(
            tracking_id="EVT1",
            timestamp=datetime(2026, 5, 21, 14, 30),
            description="In transit",
            location="Tampere",
        ),
    ]
    await repo.add_events(events)

    retrieved = await repo.get_events("EVT1")
    assert len(retrieved) == 2
    # Should be newest first
    assert retrieved[0].description == "In transit"
    assert retrieved[1].description == "Shipment registered"


@pytest.mark.asyncio
async def test_replace_events(repo: PackageRepository):
    """Test replacing all events for a package."""
    await repo.create(PackageRow(tracking_id="REP1", vendor="posti"))

    # Add initial events
    await repo.add_events([
        TrackingEventRow(
            tracking_id="REP1",
            timestamp=datetime(2026, 5, 20, 10, 0),
            description="Old event",
        ),
    ])

    # Replace with new events
    new_events = [
        TrackingEventRow(
            tracking_id="REP1",
            timestamp=datetime(2026, 5, 22, 10, 0),
            description="New event 1",
        ),
        TrackingEventRow(
            tracking_id="REP1",
            timestamp=datetime(2026, 5, 23, 10, 0),
            description="New event 2",
        ),
    ]
    await repo.replace_events("REP1", new_events)

    retrieved = await repo.get_events("REP1")
    assert len(retrieved) == 2
    assert retrieved[0].description == "New event 2"


@pytest.mark.asyncio
async def test_cascade_delete_events(repo: PackageRepository):
    """Test that deleting a package cascades to events."""
    await repo.create(PackageRow(tracking_id="CAS1", vendor="posti"))
    await repo.add_events([
        TrackingEventRow(
            tracking_id="CAS1",
            timestamp=datetime(2026, 5, 20, 10, 0),
            description="Event",
        ),
    ])

    await repo.delete("CAS1")
    events = await repo.get_events("CAS1")
    assert len(events) == 0


# --- Discovered packages tests ---


@pytest.mark.asyncio
async def test_add_and_get_discovered(repo: PackageRepository):
    """Test adding and retrieving discovered packages."""
    await repo.add_discovered(
        tracking_id="DISC1",
        vendor="posti",
        source_subject="Your package is on the way",
        source_sender="noreply@posti.fi",
    )

    discovered = await repo.get_discovered()
    assert len(discovered) == 1
    assert discovered[0]["tracking_id"] == "DISC1"
    assert discovered[0]["vendor"] == "posti"


@pytest.mark.asyncio
async def test_remove_discovered(repo: PackageRepository):
    """Test removing a discovered package."""
    await repo.add_discovered(tracking_id="DISC2", vendor="posti")

    removed = await repo.remove_discovered("DISC2")
    assert removed is True

    discovered = await repo.get_discovered()
    assert len(discovered) == 0


# --- Settings repository tests ---


@pytest.mark.asyncio
async def test_get_default_setting(settings_repo: SettingsRepository):
    """Test that default values are returned for unset keys."""
    value = await settings_repo.get_int("poll_interval_minutes", default=60)
    assert value == 60


@pytest.mark.asyncio
async def test_set_and_get_setting(settings_repo: SettingsRepository):
    """Test setting and retrieving a value."""
    await settings_repo.set("poll_interval_minutes", "30")
    value = await settings_repo.get_int("poll_interval_minutes")
    assert value == 30


@pytest.mark.asyncio
async def test_set_and_get_json(settings_repo: SettingsRepository):
    """Test JSON setting storage."""
    data = {"enabled": True, "devices": ["mobile_app_phone"]}
    await settings_repo.set_json("notifications", data)

    retrieved = await settings_repo.get_json("notifications")
    assert retrieved == data


@pytest.mark.asyncio
async def test_get_all_settings(settings_repo: SettingsRepository):
    """Test getting all settings with defaults."""
    await settings_repo.set("poll_interval_minutes", "45")

    all_settings = await settings_repo.get_all()
    assert all_settings["poll_interval_minutes"] == "45"
    # Should still have defaults for other keys
    assert "notifications" in all_settings
