"""Postnord scraper stub — implemented in task 4.2."""

from __future__ import annotations

import aiohttp

from ..models import TrackingResult
from .base import BaseScraper


class PostnordScraper(BaseScraper):
    """Scraper for Postnord."""

    async def fetch(
        self,
        tracking_id: str,
        session: aiohttp.ClientSession,
    ) -> TrackingResult:
        raise NotImplementedError
