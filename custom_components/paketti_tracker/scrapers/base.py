"""Abstract base scraper and ScraperError for Paketti Tracker."""

from __future__ import annotations

from abc import ABC, abstractmethod

import aiohttp

from ..models import TrackingResult


class ScraperError(Exception):
    """Raised when a scraper fails to retrieve or parse tracking data."""


class BaseScraper(ABC):
    """Abstract base class for carrier scrapers."""

    @abstractmethod
    async def fetch(
        self,
        tracking_id: str,
        session: aiohttp.ClientSession,
    ) -> TrackingResult:
        """Fetch tracking data for *tracking_id* using *session*.

        Returns a :class:`TrackingResult` on success.
        Raises :class:`ScraperError` on any network or parse failure.
        """
