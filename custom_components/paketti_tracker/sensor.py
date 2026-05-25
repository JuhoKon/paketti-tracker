"""Sensor platform for Paketti Tracker."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_DELIVERED,
    ATTR_ESTIMATED_DELIVERY,
    ATTR_EVENTS,
    ATTR_LAST_EVENT_TIME,
    ATTR_LAST_LOCATION,
    ATTR_PACKAGE_NAME,
    ATTR_TRACKING_ID,
    ATTR_VENDOR,
    CONF_NAME,
    CONF_PACKAGES,
    CONF_TRACKING_ID,
    CONF_VENDOR,
    DOMAIN,
    MAX_EVENTS,
    VENDOR_NAMES,
)
from .coordinator import PakettiCoordinator
from .models import TrackingResult

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities from a config entry."""
    coordinator: PakettiCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Track which entities we've already created.
    tracked_ids: set[str] = set()

    @callback
    def _async_add_new_entities() -> None:
        """Add entities for any newly configured packages."""
        packages = entry.options.get(CONF_PACKAGES, [])
        new_entities: list[PakettiSensor] = []

        for pkg in packages:
            tracking_id = pkg[CONF_TRACKING_ID]
            if tracking_id not in tracked_ids:
                tracked_ids.add(tracking_id)
                new_entities.append(
                    PakettiSensor(
                        coordinator=coordinator,
                        tracking_id=tracking_id,
                        vendor=pkg[CONF_VENDOR],
                        package_name=pkg.get(CONF_NAME, tracking_id),
                    )
                )

        if new_entities:
            async_add_entities(new_entities)

    # Create entities for existing packages.
    _async_add_new_entities()

    # Listen for options updates to add new entities.
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update — reload to pick up added/removed packages."""
    await hass.config_entries.async_reload(entry.entry_id)


class PakettiSensor(CoordinatorEntity[PakettiCoordinator], SensorEntity):
    """Sensor entity representing a single tracked package."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PakettiCoordinator,
        tracking_id: str,
        vendor: str,
        package_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._tracking_id = tracking_id
        self._vendor = vendor
        self._package_name = package_name

        self._attr_unique_id = f"{DOMAIN}_{tracking_id}"
        self._attr_name = package_name
        self._attr_icon = "mdi:package-variant"

    @property
    def available(self) -> bool:
        """Return True if coordinator has data for this package."""
        if not self.coordinator.last_update_success:
            return False
        data = self.coordinator.data
        if data is None:
            return False
        return self._tracking_id in data

    @property
    def native_value(self) -> str | None:
        """Return the normalized tracking status."""
        result = self._get_result()
        if result is None:
            return None
        return result.status

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        result = self._get_result()
        if result is None:
            return {}

        attrs: dict[str, Any] = {
            ATTR_TRACKING_ID: result.tracking_id,
            ATTR_VENDOR: VENDOR_NAMES.get(result.vendor, result.vendor),
            ATTR_PACKAGE_NAME: self._package_name,
            ATTR_DELIVERED: result.delivered,
        }

        if result.estimated_delivery:
            attrs[ATTR_ESTIMATED_DELIVERY] = result.estimated_delivery.isoformat()

        if result.last_location:
            attrs[ATTR_LAST_LOCATION] = result.last_location

        if result.last_event_time:
            attrs[ATTR_LAST_EVENT_TIME] = result.last_event_time.isoformat()

        if result.events:
            attrs[ATTR_EVENTS] = [ev.as_dict() for ev in result.events[:MAX_EVENTS]]

        return attrs

    def _get_result(self) -> TrackingResult | None:
        """Get the tracking result for this package from coordinator data."""
        data = self.coordinator.data
        if data is None:
            return None
        return data.get(self._tracking_id)
