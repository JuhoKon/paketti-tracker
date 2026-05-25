"""Abstract base scraper and shared types for carrier scrapers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime

import aiohttp


# --- Status constants ---

STATUS_UNKNOWN = "unknown"
STATUS_PENDING = "pending"
STATUS_IN_TRANSIT = "in_transit"
STATUS_OUT_FOR_DELIVERY = "out_for_delivery"
STATUS_DELIVERED = "delivered"
STATUS_EXCEPTION = "exception"

# --- Vendor constants ---

VENDOR_POSTI = "posti"
VENDOR_POSTNORD = "postnord"
VENDOR_MATKAHUOLTO = "matkahuolto"

# --- Tracking URL templates ---

TRACKING_URLS: dict[str, str] = {
    VENDOR_POSTI: "https://www.posti.fi/fi/seuranta#/lahetys/{id}",
    VENDOR_POSTNORD: "https://tracking.postnord.com/fi/?id={id}",
    VENDOR_MATKAHUOLTO: "https://www.matkahuolto.fi/seuranta/tilaus/{id}",
}


def get_tracking_url(vendor: str, tracking_id: str) -> str:
    """Build a tracking URL for the given vendor and tracking ID."""
    template = TRACKING_URLS.get(vendor, "")
    return template.replace("{id}", tracking_id) if template else ""


# --- Data classes ---


@dataclass
class TrackingEvent:
    """A single event in a package's tracking history."""

    timestamp: datetime
    description: str
    location: str | None = None


@dataclass
class TrackingResult:
    """The result of a single scrape for one package."""

    tracking_id: str
    vendor: str
    status: str
    delivered: bool
    events: list[TrackingEvent] = field(default_factory=list)
    estimated_delivery: date | None = None
    last_location: str | None = None
    last_event_time: datetime | None = None


# --- Errors ---


class ScraperError(Exception):
    """Raised when a scraper fails to retrieve or parse tracking data."""

    retryable: bool = False


class RetryableScraperError(ScraperError):
    """Raised on transient errors that may succeed on retry (timeouts, 5xx)."""

    retryable: bool = True


# --- Base class ---


class BaseScraper(ABC):
    """Abstract base class for carrier scrapers."""

    @abstractmethod
    async def fetch(
        self,
        tracking_id: str,
        session: aiohttp.ClientSession,
    ) -> TrackingResult:
        """Fetch tracking data for a tracking ID.

        Returns a TrackingResult on success.
        Raises ScraperError on any network or parse failure.
        """
