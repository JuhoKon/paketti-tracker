"""Matkahuolto scraper stub — implemented in task 5.2."""

from __future__ import annotations

import aiohttp

from ..models import TrackingResult
from .base import BaseScraper


class MatkahuoltoScraper(BaseScraper):
    """Scraper for Matkahuolto."""

    async def fetch(
        self,
        tracking_id: str,
        session: aiohttp.ClientSession,
    ) -> TrackingResult:
        raise NotImplementedError
