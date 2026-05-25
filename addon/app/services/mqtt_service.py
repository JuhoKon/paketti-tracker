"""MQTT service — publishes HA discovery configs and sensor states."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from app.db.models import PackageRow

logger = logging.getLogger(__name__)

# Topic patterns
_DISCOVERY_TOPIC = "homeassistant/sensor/paketti_tracker_{id}/config"
_STATE_TOPIC = "paketti_tracker/{id}/state"
_ATTRIBUTES_TOPIC = "paketti_tracker/{id}/attributes"
_AVAILABILITY_TOPIC = "paketti_tracker/availability"

# Device info (shared by all sensors)
_DEVICE_INFO = {
    "identifiers": ["paketti_tracker"],
    "name": "Paketti Tracker",
    "manufacturer": "Paketti Tracker Add-on",
    "model": "Package Tracker",
}


class MqttService:
    """Service for publishing package data to MQTT with HA discovery."""

    def __init__(
        self,
        host: str = "core-mosquitto",
        port: int = 1883,
        username: str = "",
        password: str = "",
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._client: Any = None
        self._connected = False
        self._task: asyncio.Task | None = None
        self._packages_cache: dict[str, PackageRow] = {}

    async def start(self) -> None:
        """Start the MQTT connection loop."""
        self._task = asyncio.create_task(self._connection_loop())
        logger.info("MQTT service starting (broker: %s:%d)", self._host, self._port)

    async def stop(self) -> None:
        """Stop MQTT and publish offline."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        if self._client and self._connected:
            try:
                await self._publish(_AVAILABILITY_TOPIC, "offline", retain=True)
            except Exception:
                pass
        self._connected = False
        logger.info("MQTT service stopped")

    async def publish_package(self, package: PackageRow) -> None:
        """Publish discovery config, state, and attributes for a package."""
        if not self._connected:
            # Cache for when we reconnect
            self._packages_cache[package.tracking_id] = package
            return

        self._packages_cache[package.tracking_id] = package

        tracking_id = package.tracking_id.lower()

        # Publish discovery config
        discovery_topic = _DISCOVERY_TOPIC.format(id=tracking_id)
        state_topic = _STATE_TOPIC.format(id=tracking_id)
        attributes_topic = _ATTRIBUTES_TOPIC.format(id=tracking_id)

        config_payload = {
            "name": package.name or package.tracking_id,
            "unique_id": f"paketti_tracker_{tracking_id}",
            "state_topic": state_topic,
            "json_attributes_topic": attributes_topic,
            "availability_topic": _AVAILABILITY_TOPIC,
            "device": _DEVICE_INFO,
            "icon": "mdi:package-variant-closed" if not package.delivered else "mdi:package-variant-closed-check",
        }

        await self._publish(discovery_topic, json.dumps(config_payload), retain=True)

        # Publish state
        await self._publish(state_topic, package.status, retain=True)

        # Publish attributes
        attributes = {
            "vendor": package.vendor,
            "name": package.name,
            "tracking_id": package.tracking_id,
            "delivered": package.delivered,
            "last_location": package.last_location,
            "last_event_time": package.last_event_time.isoformat() if package.last_event_time else None,
            "last_updated": package.last_updated.isoformat() if package.last_updated else None,
            "tracking_url": package.tracking_url,
            "estimated_delivery": package.estimated_delivery.isoformat() if package.estimated_delivery else None,
        }
        await self._publish(attributes_topic, json.dumps(attributes), retain=True)

    async def remove_package(self, tracking_id: str) -> None:
        """Remove a package sensor by publishing empty discovery config."""
        if not self._connected:
            self._packages_cache.pop(tracking_id, None)
            return

        self._packages_cache.pop(tracking_id, None)
        discovery_topic = _DISCOVERY_TOPIC.format(id=tracking_id.lower())
        await self._publish(discovery_topic, "", retain=True)

    async def republish_all(self) -> None:
        """Republish all cached packages (after reconnect)."""
        if not self._connected:
            return

        # Publish availability
        await self._publish(_AVAILABILITY_TOPIC, "online", retain=True)

        # Republish all known packages
        for package in self._packages_cache.values():
            await self.publish_package(package)

        logger.info("Republished %d package sensors", len(self._packages_cache))

    async def _connection_loop(self) -> None:
        """Maintain MQTT connection with reconnect."""
        import importlib

        while True:
            try:
                aiomqtt = importlib.import_module("aiomqtt")
                async with aiomqtt.Client(
                    hostname=self._host,
                    port=self._port,
                    username=self._username or None,
                    password=self._password or None,
                    will=aiomqtt.Will(
                        topic=_AVAILABILITY_TOPIC,
                        payload="offline",
                        retain=True,
                    ),
                ) as client:
                    self._client = client
                    self._connected = True
                    logger.info("Connected to MQTT broker")

                    # Publish online and republish all
                    await self.republish_all()

                    # Stay connected (aiomqtt context handles keepalive)
                    while True:
                        await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                self._connected = False
                self._client = None
                logger.warning("MQTT connection failed: %s. Retrying in 30s...", exc)
                await asyncio.sleep(30)

    async def _publish(self, topic: str, payload: str, retain: bool = False) -> None:
        """Publish a message to MQTT."""
        if self._client and self._connected:
            await self._client.publish(topic, payload, retain=retain)
