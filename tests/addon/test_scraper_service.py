"""Tests for scraper service and notification checker."""

from __future__ import annotations

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.database import Database
from app.db.models import PackageRow, TrackingEventRow
from app.db.repository import PackageRepository
from app.scrapers.base import TrackingEvent, TrackingResult, ScraperError, RetryableScraperError
from app.services.notification_checker import NotificationChecker, NotificationEvent
from app.services.scraper_service import ScraperService


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


# -- Notification Checker tests ---


class TestNotificationChecker:
    """Tests for NotificationChecker."""

    def setup_method(self):
        self.checker = NotificationChecker()

    def test_no_change(self):
        """No notification when status unchanged."""
        old = PackageRow(tracking_id="T1", vendor="posti", status="in_transit")
        new = PackageRow(tracking_id="T1", vendor="posti", status="in_transit")
        events = self.checker.check(old, new)
        assert events == []

    def test_new_package_no_notification(self):
        """No notification for newly added package."""
        new = PackageRow(tracking_id="T1", vendor="posti", status="unknown")
        events = self.checker.check(None, new)
        assert events == []

    def test_delivered_notification(self):
        """Delivered notification fires on delivery."""
        old = PackageRow(tracking_id="T1", vendor="posti", name="My Pkg", status="in_transit", delivered=False)
        new = PackageRow(tracking_id="T1", vendor="posti", name="My Pkg", status="delivered", delivered=True)
        events = self.checker.check(old, new)

        event_types = [e.event_type for e in events]
        assert "delivered" in event_types
        assert "status_change" in event_types

    def test_in_transit_notification(self):
        """In transit notification fires when package starts moving."""
        old = PackageRow(tracking_id="T1", vendor="posti", name="Test", status="pending")
        new = PackageRow(tracking_id="T1", vendor="posti", name="Test", status="in_transit")
        events = self.checker.check(old, new)

        event_types = [e.event_type for e in events]
        assert "in_transit" in event_types

    def test_generic_status_change(self):
        """Status change notification fires for any change."""
        old = PackageRow(tracking_id="T1", vendor="posti", status="in_transit")
        new = PackageRow(tracking_id="T1", vendor="posti", status="out_for_delivery")
        events = self.checker.check(old, new)

        assert len(events) == 1
        assert events[0].event_type == "status_change"

    def test_uses_tracking_id_as_name_fallback(self):
        """Uses tracking_id when name is empty."""
        old = PackageRow(tracking_id="JJFI123", vendor="posti", name="", status="pending")
        new = PackageRow(tracking_id="JJFI123", vendor="posti", name="", status="in_transit")
        events = self.checker.check(old, new)

        assert "JJFI123" in events[0].message


# -- Scraper Service tests ---


@pytest.mark.asyncio
async def test_poll_single_success(db, repo):
    """Test successful poll of a single package."""
    await repo.create(PackageRow(
        tracking_id="POLL1",
        vendor="posti",
        status="unknown",
    ))

    mock_result = TrackingResult(
        tracking_id="POLL1",
        vendor="posti",
        status="in_transit",
        delivered=False,
        events=[
            TrackingEvent(
                timestamp=datetime(2026, 5, 22, 10, 0),
                description="In transit",
                location="Helsinki",
            )
        ],
        last_location="Helsinki",
        last_event_time=datetime(2026, 5, 22, 10, 0),
    )

    with patch("app.services.scraper_service.get_scraper") as mock_get:
        mock_scraper = AsyncMock()
        mock_scraper.fetch = AsyncMock(return_value=mock_result)
        mock_get.return_value = mock_scraper

        service = ScraperService(db, poll_interval_minutes=60)
        service._session = MagicMock()

        notifications = await service._poll_single(repo, await repo.get_by_id("POLL1"))

    # Package should be updated
    updated = await repo.get_by_id("POLL1")
    assert updated.status == "in_transit"
    assert updated.last_location == "Helsinki"

    # Events should be stored
    events = await repo.get_events("POLL1")
    assert len(events) == 1
    assert events[0].description == "In transit"

    # Should have notifications (unknown -> in_transit)
    assert len(notifications) >= 1


@pytest.mark.asyncio
async def test_poll_single_scraper_error(db, repo):
    """Test that scraper errors don't crash the service."""
    await repo.create(PackageRow(
        tracking_id="ERR1",
        vendor="posti",
        status="unknown",
    ))

    with patch("app.services.scraper_service.get_scraper") as mock_get:
        mock_scraper = AsyncMock()
        mock_scraper.fetch = AsyncMock(side_effect=ScraperError("Network timeout"))
        mock_get.return_value = mock_scraper

        service = ScraperService(db, poll_interval_minutes=60)
        service._session = MagicMock()

        notifications = await service._poll_single(repo, await repo.get_by_id("ERR1"))

    # Should return empty notifications, not crash
    assert notifications == []

    # Package should be unchanged
    pkg = await repo.get_by_id("ERR1")
    assert pkg.status == "unknown"


@pytest.mark.asyncio
async def test_poll_skips_delivered(db, repo):
    """Test that delivered packages are skipped."""
    await repo.create(PackageRow(
        tracking_id="DONE1",
        vendor="posti",
        status="delivered",
        delivered=True,
    ))

    service = ScraperService(db, poll_interval_minutes=60)
    service._session = MagicMock()

    # get_active should not return delivered packages
    active = await repo.get_active()
    assert len(active) == 0


@pytest.mark.asyncio
async def test_notification_callback(db, repo):
    """Test that notifications trigger the callback."""
    await repo.create(PackageRow(
        tracking_id="CB1",
        vendor="posti",
        status="unknown",
    ))

    mock_result = TrackingResult(
        tracking_id="CB1",
        vendor="posti",
        status="delivered",
        delivered=True,
        events=[],
        last_location="Jyväskylä",
    )

    callback = AsyncMock()

    with patch("app.services.scraper_service.get_scraper") as mock_get:
        mock_scraper = AsyncMock()
        mock_scraper.fetch = AsyncMock(return_value=mock_result)
        mock_get.return_value = mock_scraper

        service = ScraperService(
            db,
            poll_interval_minutes=60,
            on_notifications=callback,
        )
        service._session = MagicMock()

        await service._poll_all_packages()

    # Callback should have been called with notifications
    callback.assert_called_once()
    notifications = callback.call_args[0][0]
    assert any(n.event_type == "delivered" for n in notifications)


# -- Retry Logic tests ---


@pytest.mark.asyncio
async def test_retry_on_retryable_error_then_success(db, repo):
    """Test that transient errors are retried and succeed on second attempt."""
    await repo.create(PackageRow(
        tracking_id="RETRY1",
        vendor="posti",
        status="unknown",
    ))

    mock_result = TrackingResult(
        tracking_id="RETRY1",
        vendor="posti",
        status="in_transit",
        delivered=False,
        events=[],
    )

    with patch("app.services.scraper_service.get_scraper") as mock_get, \
         patch("app.services.scraper_service.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        mock_scraper = AsyncMock()
        # First call fails with retryable error, second succeeds
        mock_scraper.fetch = AsyncMock(
            side_effect=[
                RetryableScraperError("HTTP 503"),
                mock_result,
            ]
        )
        mock_get.return_value = mock_scraper

        service = ScraperService(db, poll_interval_minutes=60)
        service._session = MagicMock()

        notifications = await service._poll_single(repo, await repo.get_by_id("RETRY1"))

    # Should have retried with 5s delay
    mock_sleep.assert_called_once_with(5)

    # Package should be updated (scraper succeeded on retry)
    updated = await repo.get_by_id("RETRY1")
    assert updated.status == "in_transit"

    # Scraper called twice
    assert mock_scraper.fetch.call_count == 2


@pytest.mark.asyncio
async def test_retry_exhausted_returns_empty(db, repo):
    """Test that after all retries exhausted, returns empty notifications."""
    await repo.create(PackageRow(
        tracking_id="RETRY2",
        vendor="posti",
        status="unknown",
    ))

    with patch("app.services.scraper_service.get_scraper") as mock_get, \
         patch("app.services.scraper_service.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        mock_scraper = AsyncMock()
        # All 3 attempts fail (initial + 2 retries)
        mock_scraper.fetch = AsyncMock(
            side_effect=RetryableScraperError("Network timeout")
        )
        mock_get.return_value = mock_scraper

        service = ScraperService(db, poll_interval_minutes=60)
        service._session = MagicMock()

        notifications = await service._poll_single(repo, await repo.get_by_id("RETRY2"))

    # No notifications
    assert notifications == []

    # Package unchanged
    pkg = await repo.get_by_id("RETRY2")
    assert pkg.status == "unknown"

    # Called 3 times total (1 initial + 2 retries)
    assert mock_scraper.fetch.call_count == 3

    # Slept twice: 5s and 15s
    assert mock_sleep.call_count == 2
    mock_sleep.assert_any_call(5)
    mock_sleep.assert_any_call(15)


@pytest.mark.asyncio
async def test_permanent_error_no_retry(db, repo):
    """Test that permanent (non-retryable) errors are not retried."""
    await repo.create(PackageRow(
        tracking_id="PERM1",
        vendor="posti",
        status="unknown",
    ))

    with patch("app.services.scraper_service.get_scraper") as mock_get, \
         patch("app.services.scraper_service.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        mock_scraper = AsyncMock()
        # Permanent error — should not retry
        mock_scraper.fetch = AsyncMock(
            side_effect=ScraperError("Tracking ID not found on Posti")
        )
        mock_get.return_value = mock_scraper

        service = ScraperService(db, poll_interval_minutes=60)
        service._session = MagicMock()

        notifications = await service._poll_single(repo, await repo.get_by_id("PERM1"))

    # No notifications
    assert notifications == []

    # Called exactly once — no retries
    assert mock_scraper.fetch.call_count == 1

    # No sleep (no retry)
    mock_sleep.assert_not_called()

    # Package unchanged
    pkg = await repo.get_by_id("PERM1")
    assert pkg.status == "unknown"


@pytest.mark.asyncio
async def test_retryable_error_class_attribute():
    """Test that RetryableScraperError has retryable=True and ScraperError has retryable=False."""
    retryable = RetryableScraperError("timeout")
    permanent = ScraperError("not found")

    assert retryable.retryable is True
    assert permanent.retryable is False
