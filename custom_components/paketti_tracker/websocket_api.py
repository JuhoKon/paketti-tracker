"""WebSocket API for Paketti Tracker panel."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.components.websocket_api import (  # type: ignore[attr-defined]
    async_register_command,
    async_response,
    websocket_command,
)
from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import (
    CONF_NAME,
    CONF_PACKAGES,
    CONF_POLL_INTERVAL,
    CONF_TRACKING_ID,
    CONF_VENDOR,
    DEFAULT_POLL_INTERVAL_MINUTES,
    DOMAIN,
    VENDORS,
)
from .coordinator import PakettiCoordinator
from .models import TrackingResult

_LOGGER = logging.getLogger(__name__)


def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register all WebSocket commands for the panel."""
    async_register_command(hass, ws_packages)
    async_register_command(hass, ws_add_package)
    async_register_command(hass, ws_remove_package)
    async_register_command(hass, ws_refresh)
    async_register_command(hass, ws_get_settings)
    async_register_command(hass, ws_update_settings)


def _get_coordinator(hass: HomeAssistant) -> PakettiCoordinator | None:
    """Get the first available coordinator."""
    domain_data: dict[str, PakettiCoordinator] = hass.data.get(DOMAIN, {})
    if not domain_data:
        return None
    # Single instance, get the first (and only) coordinator.
    return next(iter(domain_data.values()), None)


def _get_config_entry(hass: HomeAssistant) -> ConfigEntry | None:
    """Get the config entry for the integration."""
    entries = hass.config_entries.async_entries(DOMAIN)
    return entries[0] if entries else None


def _serialize_tracking_result(
    result: TrackingResult, packages: list[dict[str, Any]]
) -> dict[str, Any]:
    """Serialize a TrackingResult to a dict suitable for WS response."""
    # Get the user-defined name from the package config.
    name = result.tracking_id
    for pkg in packages:
        if pkg[CONF_TRACKING_ID] == result.tracking_id:
            name = pkg.get(CONF_NAME, result.tracking_id)
            break

    return {
        "tracking_id": result.tracking_id,
        "vendor": result.vendor,
        "name": name,
        "status": result.status,
        "delivered": result.delivered,
        "events": [event.as_dict() for event in result.events],
        "estimated_delivery": (
            result.estimated_delivery.isoformat() if result.estimated_delivery else None
        ),
        "last_location": result.last_location,
        "last_event_time": (
            result.last_event_time.isoformat() if result.last_event_time else None
        ),
    }


@websocket_command(
    {vol.Required("type"): "paketti_tracker/packages"}
)
@async_response
async def ws_packages(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Handle paketti_tracker/packages command."""
    coordinator = _get_coordinator(hass)
    if coordinator is None:
        connection.send_error(msg["id"], "not_configured", "Integration not configured")
        return

    entry = _get_config_entry(hass)
    packages_config: list[dict[str, Any]] = (
        entry.options.get(CONF_PACKAGES, []) if entry else []
    )

    data = coordinator.data or {}
    result = []
    for pkg in packages_config:
        tracking_id = pkg[CONF_TRACKING_ID]
        tracking_result = data.get(tracking_id)
        if tracking_result:
            result.append(_serialize_tracking_result(tracking_result, packages_config))
        else:
            # Package configured but no data yet.
            result.append(
                {
                    "tracking_id": tracking_id,
                    "vendor": pkg[CONF_VENDOR],
                    "name": pkg.get(CONF_NAME, tracking_id),
                    "status": "unknown",
                    "delivered": False,
                    "events": [],
                    "estimated_delivery": None,
                    "last_location": None,
                    "last_event_time": None,
                }
            )

    connection.send_result(msg["id"], {"packages": result})


@websocket_command(
    {
        vol.Required("type"): "paketti_tracker/add_package",
        vol.Required("tracking_id"): cv.string,
        vol.Required("vendor"): vol.In(VENDORS),
        vol.Optional("name", default=""): cv.string,
    }
)
@async_response
async def ws_add_package(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Handle paketti_tracker/add_package command."""
    entry = _get_config_entry(hass)
    if entry is None:
        connection.send_error(msg["id"], "not_configured", "Integration not configured")
        return

    tracking_id = msg["tracking_id"].strip().upper()
    vendor = msg["vendor"]
    name = msg.get("name", "").strip() or tracking_id

    if not tracking_id:
        connection.send_error(msg["id"], "invalid_input", "Tracking ID cannot be empty")
        return

    packages = list(entry.options.get(CONF_PACKAGES, []))
    existing_ids = {p[CONF_TRACKING_ID] for p in packages}

    if tracking_id in existing_ids:
        connection.send_error(msg["id"], "already_tracked", "Package is already being tracked")
        return

    packages.append(
        {
            CONF_TRACKING_ID: tracking_id,
            CONF_VENDOR: vendor,
            CONF_NAME: name,
        }
    )

    hass.config_entries.async_update_entry(entry, options={**entry.options, CONF_PACKAGES: packages})

    # Trigger coordinator refresh.
    coordinator = _get_coordinator(hass)
    if coordinator:
        await coordinator.async_request_refresh()

    connection.send_result(msg["id"], {"success": True, "tracking_id": tracking_id})


@websocket_command(
    {
        vol.Required("type"): "paketti_tracker/remove_package",
        vol.Required("tracking_id"): cv.string,
    }
)
@async_response
async def ws_remove_package(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Handle paketti_tracker/remove_package command."""
    entry = _get_config_entry(hass)
    if entry is None:
        connection.send_error(msg["id"], "not_configured", "Integration not configured")
        return

    tracking_id = msg["tracking_id"].strip().upper()
    packages = list(entry.options.get(CONF_PACKAGES, []))
    existing_ids = {p[CONF_TRACKING_ID] for p in packages}

    if tracking_id not in existing_ids:
        connection.send_error(msg["id"], "not_found", "Package not found")
        return

    packages = [p for p in packages if p[CONF_TRACKING_ID] != tracking_id]
    hass.config_entries.async_update_entry(entry, options={**entry.options, CONF_PACKAGES: packages})

    # Remove the entity from the entity registry.
    entity_registry = async_get_entity_registry(hass)
    entity_id = entity_registry.async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_{tracking_id}"
    )
    if entity_id:
        entity_registry.async_remove(entity_id)

    connection.send_result(msg["id"], {"success": True})


@websocket_command(
    {vol.Required("type"): "paketti_tracker/refresh"}
)
@async_response
async def ws_refresh(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Handle paketti_tracker/refresh command."""
    coordinator = _get_coordinator(hass)
    if coordinator is None:
        connection.send_error(msg["id"], "not_configured", "Integration not configured")
        return

    await coordinator.async_refresh()

    entry = _get_config_entry(hass)
    packages_config: list[dict[str, Any]] = (
        entry.options.get(CONF_PACKAGES, []) if entry else []
    )

    data = coordinator.data or {}
    result = []
    for pkg in packages_config:
        tid = pkg[CONF_TRACKING_ID]
        tracking_result = data.get(tid)
        if tracking_result:
            result.append(_serialize_tracking_result(tracking_result, packages_config))

    connection.send_result(msg["id"], {"packages": result})


@websocket_command(
    {vol.Required("type"): "paketti_tracker/get_settings"}
)
@async_response
async def ws_get_settings(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Handle paketti_tracker/get_settings command."""
    entry = _get_config_entry(hass)
    if entry is None:
        connection.send_error(msg["id"], "not_configured", "Integration not configured")
        return

    poll_interval = entry.options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL_MINUTES)
    connection.send_result(msg["id"], {"poll_interval_minutes": poll_interval})


@websocket_command(
    {
        vol.Required("type"): "paketti_tracker/update_settings",
        vol.Required("poll_interval_minutes"): vol.All(
            vol.Coerce(int), vol.Range(min=5, max=1440)
        ),
    }
)
@async_response
async def ws_update_settings(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Handle paketti_tracker/update_settings command."""
    entry = _get_config_entry(hass)
    if entry is None:
        connection.send_error(msg["id"], "not_configured", "Integration not configured")
        return

    poll_interval = msg["poll_interval_minutes"]
    hass.config_entries.async_update_entry(
        entry, options={**entry.options, CONF_POLL_INTERVAL: poll_interval}
    )

    # Update the coordinator's interval.
    coordinator = _get_coordinator(hass)
    if coordinator:
        from datetime import timedelta

        coordinator.update_interval = timedelta(minutes=poll_interval)

    connection.send_result(msg["id"], {"poll_interval_minutes": poll_interval})
