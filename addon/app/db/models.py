"""Internal database row models (dataclasses for type safety)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class PackageRow:
    """Represents a row from the packages table."""

    tracking_id: str
    vendor: str
    name: str = ""
    status: str = "unknown"
    delivered: bool = False
    last_updated: datetime | None = None
    tracking_url: str = ""
    estimated_delivery: date | None = None
    last_location: str = ""
    last_event_time: datetime | None = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TrackingEventRow:
    """Represents a row from the tracking_events table."""

    id: int | None = None
    tracking_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    description: str = ""
    location: str = ""


@dataclass
class DiscoveredPackageRow:
    """Represents a row from the discovered_packages table."""

    tracking_id: str = ""
    vendor: str = ""
    source_subject: str = ""
    source_sender: str = ""
    discovered_at: datetime = field(default_factory=datetime.now)
