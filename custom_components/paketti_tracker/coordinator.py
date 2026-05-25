"""DataUpdateCoordinator for Paketti Tracker."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_PACKAGES,
    CONF_POLL_INTERVAL,
    CONF_TRACKING_ID,
    CONF_VENDOR,
    DEFAULT_POLL_INTERVAL_MINUTES,
    DOMAIN,
)
from .models import TrackingResult
from .scrapers import get_scraper
from .scrapers.base import BaseScraper, ScraperError

_LOGGER = logging.getLogger(__name__)


class PakettiCoordinator(DataUpdateCoordinator[dict[str, TrackingResult]]):
    """Coordinator that fetches tracking data for all configured packages."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        poll_interval = entry.options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL_MINUTES)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=poll_interval),
        )
        self.config_entry = entry
        self._scrapers: dict[str, BaseScraper] = {}

    def _get_scraper(self, vendor: str) -> BaseScraper:
        """Get or create a cached scraper instance for a vendor."""
        if vendor not in self._scrapers:
            self._scrapers[vendor] = get_scraper(vendor)
        return self._scrapers[vendor]

    async def _async_update_data(self) -> dict[str, TrackingResult]:
        """Fetch tracking data for all packages."""
        packages: list[dict[str, Any]] = self.config_entry.options.get(CONF_PACKAGES, [])

        if not packages:
            return {}

        session = async_get_clientsession(self.hass)
        results: dict[str, TrackingResult] = {}

        # Preserve previous results for delivered packages (we skip polling them).
        previous_data = self.data or {}

        for pkg in packages:
            tracking_id: str = pkg[CONF_TRACKING_ID]
            vendor: str = pkg[CONF_VENDOR]

            # Skip polling for already-delivered packages.
            prev = previous_data.get(tracking_id)
            if prev and prev.delivered:
                results[tracking_id] = prev
                continue

            scraper = self._get_scraper(vendor)
            try:
                result = await scraper.fetch(tracking_id, session)
                results[tracking_id] = result
            except ScraperError as exc:
                _LOGGER.warning(
                    "Failed to fetch tracking data for %s (%s): %s",
                    tracking_id,
                    vendor,
                    exc,
                )
                # Keep previous result if available so entity doesn't go unavailable
                # on transient errors.
                if prev:
                    results[tracking_id] = prev
                # Otherwise, this tracking_id won't be in results → entity unavailable.

        return results
