"""Data models for Paketti Tracker."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class TrackingEvent:
    """A single event in a package's tracking history."""

    timestamp: datetime
    description: str
    location: str | None = None

    def as_dict(self) -> dict[str, str | None]:
        """Return a serializable dict for use as a HA attribute."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "location": self.location,
        }


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
    last_updated: datetime | None = None
