"""REST API router for settings and notification configuration."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from app.db.settings_repository import SettingsRepository
from app.main import get_database
from app.models import (
    NotificationConfig,
    NotificationConfigUpdate,
    NotificationTrigger,
    SettingsResponse,
    SettingsUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["settings"])


def _get_settings_repo() -> SettingsRepository:
    return SettingsRepository(get_database())


@router.get("/settings")
async def get_settings() -> SettingsResponse:
    """Get general application settings."""
    repo = _get_settings_repo()
    poll = await repo.get_int("poll_interval_minutes", default=60)
    email_poll = await repo.get_int("email_poll_interval_minutes", default=30)
    return SettingsResponse(
        poll_interval_minutes=poll,
        email_poll_interval_minutes=email_poll,
    )


@router.patch("/settings")
async def update_settings(body: SettingsUpdate) -> SettingsResponse:
    """Update general settings."""
    repo = _get_settings_repo()

    if body.poll_interval_minutes is not None:
        await repo.set("poll_interval_minutes", str(body.poll_interval_minutes))
    if body.email_poll_interval_minutes is not None:
        await repo.set("email_poll_interval_minutes", str(body.email_poll_interval_minutes))

    return await get_settings()


@router.get("/notifications")
async def get_notifications() -> NotificationConfig:
    """Get notification configuration."""
    repo = _get_settings_repo()
    data = await repo.get_json("notifications")
    if data is None:
        return NotificationConfig()

    triggers = [
        NotificationTrigger(**t) for t in data.get("triggers", [])
    ]
    return NotificationConfig(
        enabled=data.get("enabled", True),
        devices=data.get("devices", []),
        triggers=triggers,
    )


@router.patch("/notifications")
async def update_notifications(body: NotificationConfigUpdate) -> NotificationConfig:
    """Update notification configuration."""
    repo = _get_settings_repo()
    current = await repo.get_json("notifications") or {
        "enabled": True,
        "devices": [],
        "triggers": [],
    }

    if body.enabled is not None:
        current["enabled"] = body.enabled
    if body.devices is not None:
        current["devices"] = body.devices
    if body.triggers is not None:
        current["triggers"] = [t.model_dump() for t in body.triggers]

    await repo.set_json("notifications", current)
    return await get_notifications()
