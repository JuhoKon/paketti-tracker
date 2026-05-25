"""HA notification service — calls HA REST API to send push notifications."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from app.db.settings_repository import SettingsRepository
from app.database import Database
from app.services.notification_checker import NotificationEvent

logger = logging.getLogger(__name__)


class NotifyService:
    """Sends notifications via HA's REST API using SUPERVISOR_TOKEN."""

    def __init__(
        self,
        database: Database,
        supervisor_token: str,
        ha_api_url: str = "http://supervisor/core/api",
    ) -> None:
        self._database = database
        self._token = supervisor_token
        self._api_url = ha_api_url.rstrip("/")
        self._session: aiohttp.ClientSession | None = None

    async def start(self) -> None:
        """Initialize HTTP session."""
        self._session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            }
        )

    async def stop(self) -> None:
        """Close HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None

    async def send_notifications(self, events: list[NotificationEvent]) -> None:
        """Process notification events according to configuration.

        Checks notification config (enabled, triggers, devices) and sends
        matching notifications to configured devices.
        """
        if not events:
            return

        # Load notification config
        settings_repo = SettingsRepository(self._database)
        config = await settings_repo.get_json("notifications")
        if not config or not config.get("enabled", True):
            return

        devices = config.get("devices", [])
        if not devices:
            logger.debug("No notification devices configured")
            return

        # Build trigger map: event_type -> enabled
        triggers = {
            t["event_type"]: t.get("enabled", True)
            for t in config.get("triggers", [])
        }

        for event in events:
            # Check if this event type is enabled
            if not triggers.get(event.event_type, False):
                continue

            # Send to each device
            for device in devices:
                await self._send_to_device(device, event)

    async def _send_to_device(self, device: str, event: NotificationEvent) -> None:
        """Send a single notification to a device via HA REST API."""
        if not self._session:
            logger.warning("NotifyService not started, cannot send")
            return

        # HA notify service endpoint
        service_name = f"mobile_app_{device}" if not device.startswith("mobile_app_") else device
        url = f"{self._api_url}/services/notify/{service_name}"

        payload: dict[str, Any] = {
            "message": event.message,
            "title": "Paketti Tracker",
            "data": {
                "tag": f"paketti_{event.tracking_id}",
                "group": "paketti_tracker",
            },
        }

        try:
            async with self._session.post(url, json=payload) as resp:
                if resp.status == 200:
                    logger.debug("Notification sent to %s: %s", device, event.event_type)
                else:
                    body = await resp.text()
                    logger.warning(
                        "Failed to send notification to %s: HTTP %d - %s",
                        device, resp.status, body
                    )
        except aiohttp.ClientError as exc:
            logger.warning("Network error sending notification to %s: %s", device, exc)
