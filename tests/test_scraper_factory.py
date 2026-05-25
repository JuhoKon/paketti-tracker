"""Tests for the scraper factory."""

import pytest

from custom_components.paketti_tracker.const import (
    VENDOR_MATKAHUOLTO,
    VENDOR_POSTI,
    VENDOR_POSTNORD,
)
from custom_components.paketti_tracker.scrapers import get_scraper
from custom_components.paketti_tracker.scrapers.matkahuolto import MatkahuoltoScraper
from custom_components.paketti_tracker.scrapers.posti import PostiScraper
from custom_components.paketti_tracker.scrapers.postnord import PostnordScraper


def test_get_scraper_posti():
    scraper = get_scraper(VENDOR_POSTI)
    assert isinstance(scraper, PostiScraper)


def test_get_scraper_postnord():
    scraper = get_scraper(VENDOR_POSTNORD)
    assert isinstance(scraper, PostnordScraper)


def test_get_scraper_matkahuolto():
    scraper = get_scraper(VENDOR_MATKAHUOLTO)
    assert isinstance(scraper, MatkahuoltoScraper)


def test_get_scraper_unknown_raises():
    with pytest.raises(ValueError, match="Unknown vendor"):
        get_scraper("dhl")


def test_get_scraper_empty_string_raises():
    with pytest.raises(ValueError, match="Unknown vendor"):
        get_scraper("")
