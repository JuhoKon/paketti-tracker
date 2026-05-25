"""Tests for PakettiCoordinator."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.paketti_tracker.const import (
    CONF_PACKAGES,
    CONF_TRACKING_ID,
    CONF_VENDOR,
    STATUS_DELIVERED,
    STATUS_IN_TRANSIT,
    VENDOR_POSTI,
)
from custom_components.paketti_tracker.coordinator import PakettiCoordinator
from custom_components.paketti_tracker.models import TrackingEvent, TrackingResult
from custom_components.paketti_tracker.scrapers.base import ScraperError


def _make_result(
    tracking_id: str, status: str = STATUS_IN_TRANSIT, delivered: bool = False
) -> TrackingResult:
    """Create a minimal TrackingResult for testing."""
    return TrackingResult(
        tracking_id=tracking_id,
        vendor=VENDOR_POSTI,
        status=status,
        delivered=delivered,
        events=[
            TrackingEvent(
                timestamp=datetime(2026, 5, 22, 10, 0, 0, tzinfo=UTC),
                description="Test event",
                location="HELSINKI",
            )
        ],
    )


def _make_coordinator(packages: list[dict]) -> tuple[PakettiCoordinator, MagicMock]:
    """Create a coordinator with mocked hass and entry."""
    hass = MagicMock()
    hass.data = {}

    entry = MagicMock()
    entry.options = {CONF_PACKAGES: packages}
    entry.entry_id = "test_entry"

    coordinator = PakettiCoordinator(hass, entry)
    return coordinator, hass


@pytest.mark.asyncio
async def test_update_fetches_all_packages():
    """Test that update fetches data for all configured packages."""
    packages = [
        {CONF_TRACKING_ID: "PKG1", CONF_VENDOR: VENDOR_POSTI},
        {CONF_TRACKING_ID: "PKG2", CONF_VENDOR: VENDOR_POSTI},
    ]
    coordinator, hass = _make_coordinator(packages)

    mock_scraper = AsyncMock()
    mock_scraper.fetch = AsyncMock(side_effect=[_make_result("PKG1"), _make_result("PKG2")])

    with (
        patch(
            "custom_components.paketti_tracker.coordinator.get_scraper",
            return_value=mock_scraper,
        ),
        patch(
            "custom_components.paketti_tracker.coordinator.async_get_clientsession",
            return_value=MagicMock(),
        ),
    ):
        results = await coordinator._async_update_data()

    assert "PKG1" in results
    assert "PKG2" in results
    assert results["PKG1"].status == STATUS_IN_TRANSIT
    assert mock_scraper.fetch.call_count == 2


@pytest.mark.asyncio
async def test_update_skips_delivered():
    """Test that delivered packages are not re-polled."""
    packages = [
        {CONF_TRACKING_ID: "PKG_DELIVERED", CONF_VENDOR: VENDOR_POSTI},
        {CONF_TRACKING_ID: "PKG_ACTIVE", CONF_VENDOR: VENDOR_POSTI},
    ]
    coordinator, hass = _make_coordinator(packages)

    # Simulate previous data with a delivered package.
    coordinator.data = {
        "PKG_DELIVERED": _make_result("PKG_DELIVERED", STATUS_DELIVERED, delivered=True),
    }

    mock_scraper = AsyncMock()
    mock_scraper.fetch = AsyncMock(return_value=_make_result("PKG_ACTIVE"))

    with (
        patch(
            "custom_components.paketti_tracker.coordinator.get_scraper",
            return_value=mock_scraper,
        ),
        patch(
            "custom_components.paketti_tracker.coordinator.async_get_clientsession",
            return_value=MagicMock(),
        ),
    ):
        results = await coordinator._async_update_data()

    # Delivered package preserved without re-fetch.
    assert results["PKG_DELIVERED"].delivered is True
    # Active package was fetched.
    assert results["PKG_ACTIVE"].status == STATUS_IN_TRANSIT
    # Only one fetch call (for the active package).
    assert mock_scraper.fetch.call_count == 1


@pytest.mark.asyncio
async def test_update_partial_failure_keeps_previous():
    """Test that a failed fetch preserves previous result."""
    packages = [
        {CONF_TRACKING_ID: "PKG_OK", CONF_VENDOR: VENDOR_POSTI},
        {CONF_TRACKING_ID: "PKG_FAIL", CONF_VENDOR: VENDOR_POSTI},
    ]
    coordinator, hass = _make_coordinator(packages)

    # Previous data for the package that will fail.
    prev_result = _make_result("PKG_FAIL")
    coordinator.data = {"PKG_FAIL": prev_result}

    mock_scraper = AsyncMock()
    mock_scraper.fetch = AsyncMock(
        side_effect=[_make_result("PKG_OK"), ScraperError("Network timeout")]
    )

    with (
        patch(
            "custom_components.paketti_tracker.coordinator.get_scraper",
            return_value=mock_scraper,
        ),
        patch(
            "custom_components.paketti_tracker.coordinator.async_get_clientsession",
            return_value=MagicMock(),
        ),
    ):
        results = await coordinator._async_update_data()

    assert results["PKG_OK"].status == STATUS_IN_TRANSIT
    # Failed package retains previous result.
    assert results["PKG_FAIL"] is prev_result


@pytest.mark.asyncio
async def test_update_failure_no_previous_data():
    """Test that a failed fetch with no previous data excludes the package."""
    packages = [
        {CONF_TRACKING_ID: "PKG_FAIL", CONF_VENDOR: VENDOR_POSTI},
    ]
    coordinator, hass = _make_coordinator(packages)
    coordinator.data = {}

    mock_scraper = AsyncMock()
    mock_scraper.fetch = AsyncMock(side_effect=ScraperError("Not found"))

    with (
        patch(
            "custom_components.paketti_tracker.coordinator.get_scraper",
            return_value=mock_scraper,
        ),
        patch(
            "custom_components.paketti_tracker.coordinator.async_get_clientsession",
            return_value=MagicMock(),
        ),
    ):
        results = await coordinator._async_update_data()

    # Package not in results → entity will be unavailable.
    assert "PKG_FAIL" not in results


@pytest.mark.asyncio
async def test_update_empty_packages():
    """Test that empty package list returns empty dict."""
    coordinator, hass = _make_coordinator([])

    results = await coordinator._async_update_data()
    assert results == {}
