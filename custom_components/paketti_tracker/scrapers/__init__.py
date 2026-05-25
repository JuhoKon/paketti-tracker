"""Scraper factory for Paketti Tracker."""

from __future__ import annotations

from ..const import VENDOR_MATKAHUOLTO, VENDOR_POSTI, VENDOR_POSTNORD
from .base import BaseScraper


def get_scraper(vendor: str) -> BaseScraper:
    """Return the scraper instance for *vendor*.

    Raises :exc:`ValueError` for unknown vendor strings.
    """
    # Import here to avoid circular imports and to keep scraper modules lazy.
    from .matkahuolto import MatkahuoltoScraper
    from .posti import PostiScraper
    from .postnord import PostnordScraper

    scrapers: dict[str, BaseScraper] = {
        VENDOR_POSTI: PostiScraper(),
        VENDOR_POSTNORD: PostnordScraper(),
        VENDOR_MATKAHUOLTO: MatkahuoltoScraper(),
    }

    if vendor not in scrapers:
        raise ValueError(f"Unknown vendor: {vendor!r}. Supported vendors: {list(scrapers)}")

    return scrapers[vendor]
