"""REST API router for email configuration and discovered packages."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.db.repository import PackageRepository
from app.db.models import PackageRow
from app.main import get_database, get_settings
from app.models import (
    DiscoveredPackageResponse,
    EmailConfigResponse,
    EmailTestResponse,
)
from app.scrapers.base import get_tracking_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email", tags=["email"])


def _get_package_repo() -> PackageRepository:
    return PackageRepository(get_database())


@router.get("")
async def get_email_config() -> EmailConfigResponse:
    """Get email/IMAP configuration from add-on options (read-only)."""
    settings = get_settings()
    return EmailConfigResponse(
        enabled=settings.email_enabled,
        host=settings.email_host,
        port=settings.email_port,
        username=settings.email_username,
        password_set=bool(settings.email_password),
        folder=settings.email_folder,
        auto_add=settings.email_auto_add,
    )


@router.patch("")
async def update_email_config():
    """Email config is managed via HA add-on Options. Not writable via API."""
    return JSONResponse(
        status_code=405,
        content={"detail": "Email configuration is managed via Home Assistant add-on Options. Restart the add-on after changing options."},
    )


@router.put("")
async def put_email_config():
    """Email config is managed via HA add-on Options. Not writable via API."""
    return JSONResponse(
        status_code=405,
        content={"detail": "Email configuration is managed via Home Assistant add-on Options. Restart the add-on after changing options."},
    )


@router.post("/test")
async def test_email_connection() -> EmailTestResponse:
    """Test the IMAP connection with current config."""
    settings = get_settings()
    if not settings.email_host:
        return EmailTestResponse(success=False, message="Email not configured")

    from app.email.client import EmailClient, EmailClientError

    client = EmailClient(
        server=settings.email_host,
        port=settings.email_port,
        username=settings.email_username,
        password=settings.email_password,
        folder=settings.email_folder,
    )
    try:
        await client.connect()
        await client.disconnect()
        return EmailTestResponse(success=True, message="Connection successful")
    except EmailClientError as exc:
        return EmailTestResponse(success=False, message=str(exc))


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


@router.delete("/discovered/{tracking_id}", status_code=204, response_model=None)
async def dismiss_discovered(tracking_id: str):
    """Dismiss a discovered package without tracking it."""
    pkg_repo = _get_package_repo()
    removed = await pkg_repo.remove_discovered(tracking_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Discovered package not found")
