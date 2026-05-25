"""Pydantic models for API request/response validation."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


# --- Package models ---


class PackageCreate(BaseModel):
    """Request body for creating a new tracked package."""

    tracking_id: str = Field(..., min_length=1, description="Carrier tracking ID")
    vendor: str = Field(..., min_length=1, description="Carrier name (e.g. 'posti')")
    name: str = Field(default="", description="User-friendly name for the package")


class PackageUpdate(BaseModel):
    """Request body for updating a package (partial)."""

    name: str | None = None
    vendor: str | None = None


class TrackingEventResponse(BaseModel):
    """A single tracking event."""

    timestamp: datetime
    description: str
    location: str


class PackageResponse(BaseModel):
    """Full package response with events."""

    tracking_id: str
    vendor: str
    name: str
    status: str
    delivered: bool
    last_updated: datetime | None
    tracking_url: str
    estimated_delivery: date | None
    last_location: str
    last_event_time: datetime | None
    created_at: datetime
    events: list[TrackingEventResponse] = Field(default_factory=list)


# --- Settings models ---


class SettingsResponse(BaseModel):
    """General settings response."""

    poll_interval_minutes: int = 60
    email_poll_interval_minutes: int = 30


class SettingsUpdate(BaseModel):
    """Partial update for settings."""

    poll_interval_minutes: int | None = None
    email_poll_interval_minutes: int | None = None


# --- Notification models ---


class NotificationTrigger(BaseModel):
    """A single notification trigger."""

    event_type: str  # e.g. "status_change", "delivered", "in_transit"
    enabled: bool = True


class NotificationConfig(BaseModel):
    """Notification configuration."""

    enabled: bool = True
    devices: list[str] = Field(default_factory=list)
    triggers: list[NotificationTrigger] = Field(default_factory=list)


class NotificationConfigUpdate(BaseModel):
    """Partial update for notification config."""

    enabled: bool | None = None
    devices: list[str] | None = None
    triggers: list[NotificationTrigger] | None = None


# --- Email models ---


class EmailConfig(BaseModel):
    """Email/IMAP configuration."""

    enabled: bool = False
    host: str = ""
    port: int = 993
    username: str = ""
    password: str = ""  # Masked in GET responses
    folder: str = "INBOX"
    auto_add: bool = False


class EmailConfigResponse(BaseModel):
    """Email config response with masked password."""

    enabled: bool = False
    host: str = ""
    port: int = 993
    username: str = ""
    password_set: bool = False
    folder: str = "INBOX"
    auto_add: bool = False


class EmailConfigUpdate(BaseModel):
    """Partial update for email config."""

    enabled: bool | None = None
    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    folder: str | None = None
    auto_add: bool | None = None


class EmailTestResponse(BaseModel):
    """Response from email connection test."""

    success: bool
    message: str


# --- Discovered package models ---


class DiscoveredPackageResponse(BaseModel):
    """A package discovered from email."""

    tracking_id: str
    vendor: str
    source_subject: str
    source_sender: str
    discovered_at: datetime
