"""REST API router for email configuration and discovered packages."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.db.repository import PackageRepository
from app.db.models import PackageRow
from app.db.settings_repository import SettingsRepository
from app.main import get_database
from app.models import (
    DiscoveredPackageResponse,
    EmailConfig,
    EmailConfigResponse,
    EmailConfigUpdate,
    EmailTestResponse,
)
from app.scrapers.base import get_tracking_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email", tags=["email"])


def _get_settings_repo() -> SettingsRepository:
    return SettingsRepository(get_database())


def _get_package_repo() -> PackageRepository:
    return PackageRepository(get_database())


@router.get("")
async def get_email_config() -> EmailConfigResponse:
    """Get email/IMAP configuration (password masked)."""
    repo = _get_settings_repo()
    data = await repo.get_json("email")
    if data is None:
        return EmailConfigResponse()

    return EmailConfigResponse(
        enabled=data.get("enabled", False),
        host=data.get("host", ""),
        port=data.get("port", 993),
        username=data.get("username", ""),
        password_set=bool(data.get("password", "")),
        folder=data.get("folder", "INBOX"),
        auto_add=data.get("auto_add", False),
    )


@router.patch("")
async def update_email_config(body: EmailConfigUpdate) -> EmailConfigResponse:
    """Update email/IMAP configuration."""
    repo = _get_settings_repo()
    current = await repo.get_json("email") or {
        "enabled": False,
        "host": "",
        "port": 993,
        "username": "",
        "password": "",
        "folder": "INBOX",
        "auto_add": False,
    }

    if body.enabled is not None:
        current["enabled"] = body.enabled
    if body.host is not None:
        current["host"] = body.host
    if body.port is not None:
        current["port"] = body.port
    if body.username is not None:
        current["username"] = body.username
    if body.password is not None:
        current["password"] = body.password
    if body.folder is not None:
        current["folder"] = body.folder
    if body.auto_add is not None:
        current["auto_add"] = body.auto_add

    await repo.set_json("email", current)
    return await get_email_config()


@router.post("/test")
async def test_email_connection() -> EmailTestResponse:
    """Test the IMAP connection with current config."""
    repo = _get_settings_repo()
    data = await repo.get_json("email")
    if not data or not data.get("host"):
        return EmailTestResponse(success=False, message="Email not configured")

    # TODO: Wire to email client when available
    return EmailTestResponse(success=False, message="Email client not yet implemented")


@router.get("/discovered")
async def list_discovered() -> list[DiscoveredPackageResponse]:
    """List packages discovered from email."""
    pkg_repo = _get_package_repo()
    rows = await pkg_repo.get_discovered()
    return [
        DiscoveredPackageResponse(
            tracking_id=row["tracking_id"],
            vendor=row["vendor"],
            source_subject=row["source_subject"],
            source_sender=row["source_sender"],
            discovered_at=row["discovered_at"],
        )
        for row in rows
    ]


@router.post("/discovered/{tracking_id}/confirm", status_code=201)
async def confirm_discovered(tracking_id: str) -> dict:
    """Confirm a discovered package (add to tracking, remove from discovered)."""
    pkg_repo = _get_package_repo()

    # Find the discovered package
    discovered = await pkg_repo.get_discovered()
    match = next((d for d in discovered if d["tracking_id"] == tracking_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Discovered package not found")

    # Check if already tracked
    existing = await pkg_repo.get_by_id(tracking_id)
    if existing:
        # Already tracked, just remove from discovered
        await pkg_repo.remove_discovered(tracking_id)
        return {"message": "Package already tracked, removed from discovered"}

    # Add to tracked packages
    from datetime import datetime

    tracking_url = get_tracking_url(match["vendor"], tracking_id)
    package = PackageRow(
        tracking_id=tracking_id,
        vendor=match["vendor"],
        name="",
        tracking_url=tracking_url,
        created_at=datetime.now(),
    )
    await pkg_repo.create(package)

    # Remove from discovered
    await pkg_repo.remove_discovered(tracking_id)

    return {"message": "Package added to tracking"}


@router.delete("/discovered/{tracking_id}", status_code=204)
async def dismiss_discovered(tracking_id: str) -> None:
    """Dismiss a discovered package without tracking it."""
    pkg_repo = _get_package_repo()
    removed = await pkg_repo.remove_discovered(tracking_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Discovered package not found")
