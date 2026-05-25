"""Scraper service — periodic polling loop for package tracking updates."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Callable, Awaitable

import aiohttp

from app.database import Database
from app.db.models import PackageRow, TrackingEventRow
from app.db.repository import PackageRepository
from app.scrapers.base import RetryableScraperError, ScraperError, TrackingResult, get_tracking_url
from app.scrapers.factory import get_scraper
from app.services.notification_checker import NotificationChecker, NotificationEvent

logger = logging.getLogger(__name__)

# Retry configuration for transient scraper errors.
_MAX_RETRIES = 2
_RETRY_DELAYS_S = (5, 15)

# Type for the notification callback
NotifyCallback = Callable[[list[NotificationEvent]], Awaitable[None]]

# Type for the MQTT publish callback
MqttPublishCallback = Callable[[PackageRow], Awaitable[None]]


class ScraperService:
    """Background service that polls carrier APIs for package updates."""

    def __init__(
        self,
        database: Database,
        poll_interval_minutes: int = 60,
        on_notifications: NotifyCallback | None = None,
        on_package_updated: MqttPublishCallback | None = None,
    ) -> None:
        self._database = database
        self._poll_interval = poll_interval_minutes * 60  # Convert to seconds
        self._task: asyncio.Task | None = None
        self._session: aiohttp.ClientSession | None = None
        self._notification_checker = NotificationChecker()
        self._on_notifications = on_notifications
        self._on_package_updated = on_package_updated
        self._running = False

    async def start(self) -> None:
        """Start the polling loop."""
        self._running = True
        self._session = aiohttp.ClientSession()
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("Scraper service started (interval: %ds)", self._poll_interval)

    async def stop(self) -> None:
        """Stop the polling loop and clean up."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        if self._session:
            await self._session.close()
            self._session = None
        logger.info("Scraper service stopped")

    async def poll_now(self) -> None:
        """Trigger an immediate poll (called from refresh endpoint)."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        await self._poll_all_packages()

    def set_poll_interval(self, minutes: int) -> None:
        """Update the poll interval dynamically."""
        self._poll_interval = minutes * 60

    async def _poll_loop(self) -> None:
        """Main polling loop — runs until cancelled."""
        # Initial poll immediately on start
        await self._poll_all_packages()

        while self._running:
            try:
                await asyncio.sleep(self._poll_interval)
                if self._running:
                    await self._poll_all_packages()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Unexpected error in poll loop")
                # Don't crash the loop — wait and retry
                await asyncio.sleep(60)

    async def _poll_all_packages(self) -> None:
        """Poll all active (non-delivered) packages."""
        repo = PackageRepository(self._database)
        packages = await repo.get_active()

        if not packages:
            logger.debug("No active packages to poll")
            return

        logger.info("Polling %d active packages", len(packages))

        all_notifications: list[NotificationEvent] = []

        for package in packages:
            try:
                notifications = await self._poll_single(repo, package)
                all_notifications.extend(notifications)
            except Exception:
                logger.exception(
                    "Error polling package %s", package.tracking_id
                )
                # Error isolation: continue with other packages

        # Fire notifications
        if all_notifications and self._on_notifications:
            try:
                await self._on_notifications(all_notifications)
            except Exception:
                logger.exception("Error sending notifications")

    async def _poll_single(
        self, repo: PackageRepository, package: PackageRow
    ) -> list[NotificationEvent]:
        """Poll a single package and update the database.

        Retries up to _MAX_RETRIES times on transient (retryable) errors with
        exponential backoff (_RETRY_DELAYS_S).
        """
        assert self._session is not None

        try:
            scraper = get_scraper(package.vendor)
        except ValueError:
            logger.warning("No scraper for vendor %s", package.vendor)
            return []

        result: TrackingResult | None = None
        last_error: ScraperError | None = None

        for attempt in range(_MAX_RETRIES + 1):
            try:
                result = await scraper.fetch(package.tracking_id, self._session)
                break  # Success
            except RetryableScraperError as exc:
                last_error = exc
                if attempt < _MAX_RETRIES:
                    delay = _RETRY_DELAYS_S[attempt]
                    logger.warning(
                        "Transient scraper error for %s (vendor=%s), attempt %d/%d, "
                        "retrying in %ds: %s",
                        package.tracking_id,
                        package.vendor,
                        attempt + 1,
                        _MAX_RETRIES + 1,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.warning(
                        "Scraper failed for %s (vendor=%s) after %d attempts: %s",
                        package.tracking_id,
                        package.vendor,
                        _MAX_RETRIES + 1,
                        exc,
                    )
            except ScraperError as exc:
                # Permanent error — no retry.
                logger.warning(
                    "Scraper error for %s (vendor=%s): %s",
                    package.tracking_id,
                    package.vendor,
                    exc,
                )
                return []

        if result is None:
            return []

        # Update package fields
        now = datetime.now()
        update_fields = {
            "status": result.status,
            "delivered": result.delivered,
            "last_updated": now,
            "last_location": result.last_location or "",
            "last_event_time": result.last_event_time,
        }
        if result.estimated_delivery:
            update_fields["estimated_delivery"] = result.estimated_delivery

        updated_package = await repo.update(package.tracking_id, **update_fields)

        # Replace events
        events = [
            TrackingEventRow(
                tracking_id=package.tracking_id,
                timestamp=e.timestamp,
                description=e.description,
                location=e.location or "",
            )
            for e in result.events
        ]
        await repo.replace_events(package.tracking_id, events)

        # Check for notifications
        notifications = self._notification_checker.check(package, updated_package)

        # Notify MQTT
        if self._on_package_updated and updated_package:
            try:
                await self._on_package_updated(updated_package)
            except Exception:
                logger.exception("Error publishing MQTT update for %s", package.tracking_id)

        logger.debug(
            "Updated %s: %s -> %s",
            package.tracking_id,
            package.status,
            result.status,
        )

        return notifications
