"""Scraper factory — instantiates the correct scraper for a vendor."""

from __future__ import annotations

from .base import BaseScraper, VENDOR_POSTI
from .posti import PostiScraper


_SCRAPERS: dict[str, type[BaseScraper]] = {
    VENDOR_POSTI: PostiScraper,
}


def get_scraper(vendor: str) -> BaseScraper:
    """Get a scraper instance for the given vendor.

    Raises ValueError if the vendor is not supported.
    """
    scraper_cls = _SCRAPERS.get(vendor)
    if scraper_cls is None:
        raise ValueError(f"Unsupported vendor: {vendor!r}. Supported: {list(_SCRAPERS.keys())}")
    return scraper_cls()


def supported_vendors() -> list[str]:
    """Return list of supported vendor names."""
    return list(_SCRAPERS.keys())
