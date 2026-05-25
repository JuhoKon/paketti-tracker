"""Tests for settings, notifications, and email REST APIs."""

from __future__ import annotations

import os

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("PAKETTI_DATA_DIR", "/tmp/paketti_settings_test")

from app.main import app


@pytest.fixture
async def client(tmp_path, monkeypatch):
    """Create a test client with lifespan initialized."""
    monkeypatch.setenv("PAKETTI_DATA_DIR", str(tmp_path))

    import app.main as main_mod
    main_mod._settings = None
    main_mod._database = None
    main_mod._ready = False

    async with LifespanManager(app) as manager:
        transport = ASGITransport(app=manager.app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


# -- Settings tests ---


@pytest.mark.asyncio
async def test_get_settings_defaults(client: AsyncClient):
    """Test default settings are returned."""
    resp = await client.get("/api/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["poll_interval_minutes"] == 60
    assert data["email_poll_interval_minutes"] == 30


@pytest.mark.asyncio
async def test_update_settings(client: AsyncClient):
    """Test updating poll interval."""
    resp = await client.patch("/api/settings", json={
        "poll_interval_minutes": 30,
    })
    assert resp.status_code == 200
    assert resp.json()["poll_interval_minutes"] == 30

    # Verify persistence
    resp = await client.get("/api/settings")
    assert resp.json()["poll_interval_minutes"] == 30


# -- Notification tests ---


@pytest.mark.asyncio
async def test_get_notifications_defaults(client: AsyncClient):
    """Test default notification config."""
    resp = await client.get("/api/notifications")
    assert resp.status_code == 200
    data = resp.json()
    assert data["enabled"] is True
    assert isinstance(data["triggers"], list)


@pytest.mark.asyncio
async def test_update_notifications(client: AsyncClient):
    """Test updating notification config."""
    resp = await client.patch("/api/notifications", json={
        "enabled": False,
        "devices": ["mobile_app_phone"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["enabled"] is False
    assert data["devices"] == ["mobile_app_phone"]


# -- Email config tests ---


@pytest.mark.asyncio
async def test_get_email_config_defaults(client: AsyncClient):
    """Test default email config."""
    resp = await client.get("/api/email")
    assert resp.status_code == 200
    data = resp.json()
    assert data["enabled"] is False
    assert data["password_set"] is False


@pytest.mark.asyncio
async def test_update_email_config(client: AsyncClient):
    """Email config is read-only via API (managed via add-on Options)."""
    resp = await client.patch("/api/email", json={
        "enabled": True,
        "host": "imap.gmail.com",
        "username": "user@gmail.com",
        "password": "secret123",
    })
    assert resp.status_code == 405
    data = resp.json()
    assert "add-on Options" in data["detail"]


@pytest.mark.asyncio
async def test_email_test_not_configured(client: AsyncClient):
    """Test email connection test when not configured."""
    resp = await client.post("/api/email/test")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False


# -- Discovered packages tests ---


@pytest.mark.asyncio
async def test_discovered_empty(client: AsyncClient):
    """Test listing discovered packages when empty."""
    resp = await client.get("/api/email/discovered")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_confirm_discovered(client: AsyncClient):
    """Test confirming a discovered package adds it to tracking."""
    # Manually add a discovered package via the repository
    from app.db.repository import PackageRepository
    from app.main import get_database

    repo = PackageRepository(get_database())
    await repo.add_discovered(
        tracking_id="DISC1",
        vendor="posti",
        source_subject="Your package",
        source_sender="posti@posti.fi",
    )

    # Confirm it
    resp = await client.post("/api/email/discovered/DISC1/confirm")
    assert resp.status_code == 201

    # Should now be in tracked packages
    resp = await client.get("/api/packages")
    ids = [p["tracking_id"] for p in resp.json()]
    assert "DISC1" in ids

    # Should be removed from discovered
    resp = await client.get("/api/email/discovered")
    assert resp.json() == []


@pytest.mark.asyncio
async def test_dismiss_discovered(client: AsyncClient):
    """Test dismissing a discovered package removes it."""
    from app.db.repository import PackageRepository
    from app.main import get_database

    repo = PackageRepository(get_database())
    await repo.add_discovered(tracking_id="DISC2", vendor="posti")

    resp = await client.delete("/api/email/discovered/DISC2")
    assert resp.status_code == 204

    resp = await client.get("/api/email/discovered")
    assert resp.json() == []


@pytest.mark.asyncio
async def test_dismiss_nonexistent(client: AsyncClient):
    """Test dismissing non-existent discovered package returns 404."""
    resp = await client.delete("/api/email/discovered/NONEXIST")
    assert resp.status_code == 404
