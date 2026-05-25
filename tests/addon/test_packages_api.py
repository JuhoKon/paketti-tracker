"""Tests for the packages REST API."""

from __future__ import annotations

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

import os
os.environ.setdefault("PAKETTI_DATA_DIR", "/tmp/paketti_api_test")

from app.main import app


@pytest.fixture
async def client(tmp_path, monkeypatch):
    """Create a test client with lifespan initialized."""
    monkeypatch.setenv("PAKETTI_DATA_DIR", str(tmp_path))

    # Re-import to pick up env change
    import app.main as main_mod
    main_mod._settings = None
    main_mod._database = None
    main_mod._ready = False

    async with LifespanManager(app) as manager:
        transport = ASGITransport(app=manager.app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest.mark.asyncio
async def test_list_packages_empty(client: AsyncClient):
    """Test listing packages when none exist."""
    resp = await client.get("/api/packages")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_add_package(client: AsyncClient):
    """Test adding a new package."""
    resp = await client.post("/api/packages", json={
        "tracking_id": "JJFI12345678",
        "vendor": "posti",
        "name": "Test Package",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["tracking_id"] == "JJFI12345678"
    assert data["vendor"] == "posti"
    assert data["name"] == "Test Package"
    assert data["status"] == "unknown"
    assert data["delivered"] is False
    assert "posti.fi" in data["tracking_url"]


@pytest.mark.asyncio
async def test_add_package_duplicate(client: AsyncClient):
    """Test adding a duplicate package returns 409."""
    await client.post("/api/packages", json={
        "tracking_id": "DUP1",
        "vendor": "posti",
    })
    resp = await client.post("/api/packages", json={
        "tracking_id": "DUP1",
        "vendor": "posti",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_add_package_missing_fields(client: AsyncClient):
    """Test adding a package with missing required fields returns 422."""
    resp = await client.post("/api/packages", json={
        "name": "Missing tracking_id",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_edit_package(client: AsyncClient):
    """Test editing a package name."""
    await client.post("/api/packages", json={
        "tracking_id": "EDIT1",
        "vendor": "posti",
        "name": "Old Name",
    })

    resp = await client.patch("/api/packages/EDIT1", json={
        "name": "New Name",
    })
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_edit_package_not_found(client: AsyncClient):
    """Test editing a non-existent package returns 404."""
    resp = await client.patch("/api/packages/NONEXIST", json={
        "name": "Whatever",
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_package(client: AsyncClient):
    """Test deleting a package."""
    await client.post("/api/packages", json={
        "tracking_id": "DEL1",
        "vendor": "posti",
    })

    resp = await client.delete("/api/packages/DEL1")
    assert resp.status_code == 204

    # Verify it's gone
    resp = await client.get("/api/packages")
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_delete_package_not_found(client: AsyncClient):
    """Test deleting a non-existent package returns 404."""
    resp = await client.delete("/api/packages/NONEXIST")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_refresh_packages(client: AsyncClient):
    """Test refresh endpoint returns 202."""
    resp = await client.post("/api/packages/refresh")
    assert resp.status_code == 202


@pytest.mark.asyncio
async def test_list_packages_with_data(client: AsyncClient):
    """Test listing packages returns correct data."""
    await client.post("/api/packages", json={
        "tracking_id": "LIST1",
        "vendor": "posti",
        "name": "First",
    })
    await client.post("/api/packages", json={
        "tracking_id": "LIST2",
        "vendor": "posti",
        "name": "Second",
    })

    resp = await client.get("/api/packages")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    ids = {p["tracking_id"] for p in data}
    assert ids == {"LIST1", "LIST2"}
