"""Email polling service — checks IMAP for new tracking IDs."""

from __future__ import annotations

import asyncio
import logging

from app.config import Settings
from app.database import Database
from app.db.models import PackageRow
from app.db.repository import PackageRepository
from app.email.client import EmailClient, EmailClientError
from app.email.parser import parse_email
from app.scrapers.base import get_tracking_url

logger = logging.getLogger(__name__)


class EmailService:
    """Background service that polls IMAP for emails containing tracking IDs."""

    def __init__(
        self,
        database: Database,
        settings: Settings,
    ) -> None:
        self._database = database
        self._settings = settings
        self._poll_interval = settings.email_poll_interval * 60
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        """Start the email polling loop."""
        if not self._settings.email_enabled or not self._settings.email_host:
            logger.info("Email service disabled (email_enabled=%s, host=%r)",
                        self._settings.email_enabled, self._settings.email_host)
            return

        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("Email service started (interval: %ds)", self._poll_interval)

    async def stop(self) -> None:
        """Stop the email polling loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Email service stopped")

    def set_poll_interval(self, minutes: int) -> None:
        """Update the poll interval dynamically."""
        self._poll_interval = minutes * 60

    async def poll_now(self) -> int:
        """Trigger an immediate poll. Returns number of discovered packages."""
        if not self._settings.email_enabled or not self._settings.email_host:
            return 0
        return await self._check_emails()

    async def _poll_loop(self) -> None:
        """Main polling loop."""
        # Initial delay before first poll (give app time to fully start)
        await asyncio.sleep(10)

        while self._running:
            try:
                await self._check_emails()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in email poll loop")

            try:
                await asyncio.sleep(self._poll_interval)
            except asyncio.CancelledError:
                break

    async def _check_emails(self) -> int:
        """Check emails and process discovered packages. Returns count."""
        client = EmailClient(
            server=self._settings.email_host,
            port=self._settings.email_port,
            username=self._settings.email_username,
            password=self._settings.email_password,
            folder=self._settings.email_folder,
        )

        try:
            await client.connect()
            uids = await client.search_recent(days=7)

            if not uids:
                return 0

            messages = await client.fetch_messages(uids)
        except EmailClientError as exc:
            logger.warning("Email check failed: %s", exc)
            return 0
        finally:
            await client.disconnect()

        # Parse emails for tracking IDs
        pkg_repo = PackageRepository(self._database)
        discovered_count = 0
        auto_add = self._settings.email_auto_add

        for msg in messages:
            discovered = parse_email(msg)
            for pkg in discovered:
                # Skip if already tracked or already discovered
                existing = await pkg_repo.get_by_id(pkg.tracking_id)
                if existing:
                    continue

                # Check if already in discovered list
                discovered_list = await pkg_repo.get_discovered()
                already_discovered = any(
                    d["tracking_id"] == pkg.tracking_id for d in discovered_list
                )
                if already_discovered:
                    continue

                if auto_add:
                    # Directly add to tracked packages
                    tracking_url = get_tracking_url(pkg.vendor, pkg.tracking_id)
                    from datetime import datetime
                    new_pkg = PackageRow(
                        tracking_id=pkg.tracking_id,
                        vendor=pkg.vendor,
                        name="",
                        tracking_url=tracking_url,
                        created_at=datetime.now(),
                    )
                    await pkg_repo.create(new_pkg)
                    logger.info("Auto-added package %s from email", pkg.tracking_id)
                else:
                    # Add to discovered queue
                    await pkg_repo.add_discovered(
                        tracking_id=pkg.tracking_id,
                        vendor=pkg.vendor,
                        source_subject=pkg.source_subject,
                        source_sender=pkg.source_sender,
                    )
                    logger.info("Discovered package %s from email", pkg.tracking_id)

                discovered_count += 1

        return discovered_count
