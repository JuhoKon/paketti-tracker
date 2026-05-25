"""REST API router for package CRUD operations."""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks

from app.database import Database
from app.db.models import PackageRow
from app.db.repository import PackageRepository
from app.main import get_database
from app.models import (
    PackageCreate,
    PackageResponse,
    PackageUpdate,
    TrackingEventResponse,
)
from app.scrapers.base import get_tracking_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/packages", tags=["packages"])


def _get_repo() -> PackageRepository:
    return PackageRepository(get_database())


def _package_to_response(pkg: PackageRow, events=None) -> PackageResponse:
    """Convert a PackageRow to a PackageResponse."""
    event_responses = []
    if events:
        event_responses = [
            TrackingEventResponse(
                timestamp=e.timestamp,
                description=e.description,
                location=e.location or "",
            )
            for e in events
        ]
    return PackageResponse(
        tracking_id=pkg.tracking_id,
        vendor=pkg.vendor,
        name=pkg.name,
        status=pkg.status,
        delivered=pkg.delivered,
        last_updated=pkg.last_updated,
        tracking_url=pkg.tracking_url,
        estimated_delivery=pkg.estimated_delivery,
        last_location=pkg.last_location,
        last_event_time=pkg.last_event_time,
        created_at=pkg.created_at,
        events=event_responses,
    )


@router.get("")
async def list_packages() -> list[PackageResponse]:
    """List all tracked packages with their events."""
    repo = _get_repo()
    packages = await repo.get_all()
    results = []
    for pkg in packages:
        events = await repo.get_events(pkg.tracking_id)
        results.append(_package_to_response(pkg, events))
    return results


@router.post("", status_code=201)
async def add_package(body: PackageCreate) -> PackageResponse:
    """Add a new package to tracking."""
    repo = _get_repo()

    # Check if already exists
    existing = await repo.get_by_id(body.tracking_id)
    if existing:
        raise HTTPException(status_code=409, detail="Package already tracked")

    tracking_url = get_tracking_url(body.vendor, body.tracking_id)
    package = PackageRow(
        tracking_id=body.tracking_id,
        vendor=body.vendor,
        name=body.name,
        tracking_url=tracking_url,
        created_at=datetime.now(),
    )
    created = await repo.create(package)
    return _package_to_response(created)


@router.patch("/{tracking_id}")
async def edit_package(tracking_id: str, body: PackageUpdate) -> PackageResponse:
    """Edit an existing package's name or vendor."""
    repo = _get_repo()

    existing = await repo.get_by_id(tracking_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Package not found")

    update_fields = {}
    if body.name is not None:
        update_fields["name"] = body.name
    if body.vendor is not None:
        update_fields["vendor"] = body.vendor
        # Recalculate tracking URL if vendor changes
        update_fields["tracking_url"] = get_tracking_url(body.vendor, tracking_id)

    if update_fields:
        updated = await repo.update(tracking_id, **update_fields)
    else:
        updated = existing

    events = await repo.get_events(tracking_id)
    return _package_to_response(updated, events)


@router.delete("/{tracking_id}", status_code=204, response_model=None)
async def delete_package(tracking_id: str):
    """Remove a tracked package."""
    repo = _get_repo()
    deleted = await repo.delete(tracking_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Package not found")


@router.post("/refresh", status_code=202)
async def refresh_packages() -> dict:
    """Trigger an immediate poll of all active packages.

    The actual scraping happens in the background.
    """
    # TODO: Wire to scraper_service when available
    return {"message": "Refresh initiated"}
