"""Notification checker — compares old/new package status and fires triggers."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.db.models import PackageRow

logger = logging.getLogger(__name__)


@dataclass
class NotificationEvent:
    """An event that should trigger a notification."""

    tracking_id: str
    package_name: str
    vendor: str
    event_type: str  # "delivered", "in_transit", "status_change"
    old_status: str
    new_status: str
    message: str


class NotificationChecker:
    """Checks whether a package update should trigger notifications."""

    def check(
        self,
        old_package: PackageRow | None,
        new_package: PackageRow,
    ) -> list[NotificationEvent]:
        """Compare old and new state, return notification events to fire.

        Returns an empty list if no notification-worthy change occurred.
        """
        if old_package is None:
            # New package — no notification
            return []

        old_status = old_package.status
        new_status = new_package.status

        if old_status == new_status:
            return []

        events: list[NotificationEvent] = []
        name = new_package.name or new_package.tracking_id

        # Delivered notification
        if new_package.delivered and not old_package.delivered:
            events.append(NotificationEvent(
                tracking_id=new_package.tracking_id,
                package_name=name,
                vendor=new_package.vendor,
                event_type="delivered",
                old_status=old_status,
                new_status=new_status,
                message=f"Package '{name}' has been delivered!",
            ))

        # In transit notification (first movement)
        elif new_status == "in_transit" and old_status in ("unknown", "pending"):
            events.append(NotificationEvent(
                tracking_id=new_package.tracking_id,
                package_name=name,
                vendor=new_package.vendor,
                event_type="in_transit",
                old_status=old_status,
                new_status=new_status,
                message=f"Package '{name}' is now in transit.",
            ))

        # Generic status change
        if old_status != new_status:
            events.append(NotificationEvent(
                tracking_id=new_package.tracking_id,
                package_name=name,
                vendor=new_package.vendor,
                event_type="status_change",
                old_status=old_status,
                new_status=new_status,
                message=f"Package '{name}' status: {old_status} → {new_status}",
            ))

        return events
