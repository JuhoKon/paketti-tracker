"""Notification dispatch for Paketti Tracker."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from homeassistant.core import HomeAssistant

from .const import (
    CONF_NOTIFICATIONS,
    CONF_NOTIFICATIONS_DEVICES,
    CONF_NOTIFICATIONS_ENABLED,
    CONF_NOTIFICATIONS_TRIGGERS,
    DEFAULT_NOTIFICATION_TRIGGERS,
    STATUS_DELIVERED,
    STATUS_EXCEPTION,
    STATUS_IN_TRANSIT,
    STATUS_OUT_FOR_DELIVERY,
    VENDOR_NAMES,
)

_LOGGER = logging.getLogger(__name__)

# Human-readable status labels for notification messages.
_STATUS_LABELS: dict[str, str] = {
    STATUS_IN_TRANSIT: "In Transit",
    STATUS_OUT_FOR_DELIVERY: "Out for Delivery",
    STATUS_DELIVERED: "Delivered",
    STATUS_EXCEPTION: "Exception",
}


def get_notification_config(options: Mapping[str, Any]) -> dict[str, Any]:
    """Get the notification configuration from entry options, with defaults."""
    config = options.get(CONF_NOTIFICATIONS, {})
    return {
        CONF_NOTIFICATIONS_ENABLED: config.get(CONF_NOTIFICATIONS_ENABLED, False),
        CONF_NOTIFICATIONS_TRIGGERS: config.get(
            CONF_NOTIFICATIONS_TRIGGERS, DEFAULT_NOTIFICATION_TRIGGERS
        ),
        CONF_NOTIFICATIONS_DEVICES: config.get(CONF_NOTIFICATIONS_DEVICES, []),
    }


async def async_send_notification(
    hass: HomeAssistant,
    package_name: str,
    vendor: str,
    new_status: str,
    event_description: str | None,
    devices: list[str],
) -> None:
    """Send a notification to configured devices via HA notify service."""
    if not devices:
        _LOGGER.debug("No notification devices configured, skipping")
        return

    vendor_label = VENDOR_NAMES.get(vendor, vendor)
    status_label = _STATUS_LABELS.get(new_status, new_status)

    title = f"Package Update: {package_name}"
    message = f"{package_name} ({vendor_label}) is now: {status_label}"
    if event_description:
        message += f"\n{event_description}"

    for device in devices:
        service_name = f"notify.{device}"
        try:
            await hass.services.async_call(
                "notify",
                device,
                {"title": title, "message": message},
                blocking=False,
            )
        except Exception:  # noqa: BLE001
            _LOGGER.warning("Failed to send notification to %s", service_name)


async def async_check_and_notify(
    hass: HomeAssistant,
    options: Mapping[str, Any],
    old_status: str | None,
    new_status: str,
    package_name: str,
    vendor: str,
    event_description: str | None,
) -> None:
    """Check if a status change should trigger a notification and send it."""
    config = get_notification_config(options)

    if not config[CONF_NOTIFICATIONS_ENABLED]:
        return

    # No notification on first poll (no old status) or no change.
    if old_status is None or old_status == new_status:
        return

    triggers: list[str] = config[CONF_NOTIFICATIONS_TRIGGERS]
    if new_status not in triggers:
        return

    devices: list[str] = config[CONF_NOTIFICATIONS_DEVICES]
    await async_send_notification(
        hass,
        package_name=package_name,
        vendor=vendor,
        new_status=new_status,
        event_description=event_description,
        devices=devices,
    )
