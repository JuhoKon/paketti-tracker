"""Email polling coordinator for Paketti Tracker."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_DISCOVERED_PACKAGES,
    CONF_EMAIL,
    CONF_EMAIL_AUTO_ADD,
    CONF_EMAIL_ENABLED,
    CONF_EMAIL_FOLDER,
    CONF_EMAIL_IMAP_PORT,
    CONF_EMAIL_IMAP_SERVER,
    CONF_EMAIL_PASSWORD,
    CONF_EMAIL_POLL_INTERVAL,
    CONF_EMAIL_SEARCH_DAYS,
    CONF_EMAIL_USERNAME,
    CONF_NAME,
    CONF_PACKAGES,
    CONF_TRACKING_ID,
    CONF_VENDOR,
    DEFAULT_EMAIL_FOLDER,
    DEFAULT_EMAIL_IMAP_PORT,
    DEFAULT_EMAIL_POLL_INTERVAL_MINUTES,
    DEFAULT_EMAIL_SEARCH_DAYS,
)
from .email_client import EmailClient, EmailClientError
from .email_parser import DiscoveredPackage, parse_email

_LOGGER = logging.getLogger(__name__)


def get_email_config(options: dict[str, Any] | Any) -> dict[str, Any]:
    """Get the email configuration from entry options, with defaults."""
    config = options.get(CONF_EMAIL, {})
    return {
        CONF_EMAIL_ENABLED: config.get(CONF_EMAIL_ENABLED, False),
        CONF_EMAIL_IMAP_SERVER: config.get(CONF_EMAIL_IMAP_SERVER, ""),
        CONF_EMAIL_IMAP_PORT: config.get(CONF_EMAIL_IMAP_PORT, DEFAULT_EMAIL_IMAP_PORT),
        CONF_EMAIL_USERNAME: config.get(CONF_EMAIL_USERNAME, ""),
        CONF_EMAIL_PASSWORD: config.get(CONF_EMAIL_PASSWORD, ""),
        CONF_EMAIL_FOLDER: config.get(CONF_EMAIL_FOLDER, DEFAULT_EMAIL_FOLDER),
        CONF_EMAIL_POLL_INTERVAL: config.get(
            CONF_EMAIL_POLL_INTERVAL, DEFAULT_EMAIL_POLL_INTERVAL_MINUTES
        ),
        CONF_EMAIL_AUTO_ADD: config.get(CONF_EMAIL_AUTO_ADD, False),
        CONF_EMAIL_SEARCH_DAYS: config.get(CONF_EMAIL_SEARCH_DAYS, DEFAULT_EMAIL_SEARCH_DAYS),
    }


async def async_poll_email(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> list[DiscoveredPackage]:
    """Poll email for new tracking IDs.

    Returns newly discovered packages (not yet tracked or previously discovered).
    """
    email_config = get_email_config(entry.options)

    if not email_config[CONF_EMAIL_ENABLED]:
        return []

    server = email_config[CONF_EMAIL_IMAP_SERVER]
    port = email_config[CONF_EMAIL_IMAP_PORT]
    username = email_config[CONF_EMAIL_USERNAME]
    password = email_config[CONF_EMAIL_PASSWORD]
    folder = email_config[CONF_EMAIL_FOLDER]
    search_days = email_config[CONF_EMAIL_SEARCH_DAYS]

    if not server or not username or not password:
        _LOGGER.debug("Email config incomplete, skipping poll")
        return []

    client = EmailClient(
        server=server,
        port=port,
        username=username,
        password=password,
        folder=folder,
    )

    try:
        await client.connect()
        uids = await client.search_recent(days=search_days)
        messages = await client.fetch_messages(uids)
        await client.disconnect()
    except EmailClientError as exc:
        _LOGGER.warning("Email polling failed: %s", exc)
        return []

    # Parse all messages for tracking IDs.
    all_discovered: list[DiscoveredPackage] = []
    for msg in messages:
        all_discovered.extend(parse_email(msg))

    # Filter out already-tracked packages.
    tracked_ids = {
        pkg[CONF_TRACKING_ID]
        for pkg in entry.options.get(CONF_PACKAGES, [])
    }

    # Filter out already-discovered (pending confirmation) packages.
    existing_discovered = entry.options.get(CONF_DISCOVERED_PACKAGES, [])
    discovered_ids = {d["tracking_id"] for d in existing_discovered}

    new_packages = [
        p for p in all_discovered
        if p.tracking_id not in tracked_ids and p.tracking_id not in discovered_ids
    ]

    # Deduplicate within this batch.
    seen: set[str] = set()
    unique_new: list[DiscoveredPackage] = []
    for p in new_packages:
        if p.tracking_id not in seen:
            seen.add(p.tracking_id)
            unique_new.append(p)

    if unique_new:
        _LOGGER.info("Discovered %d new packages from email", len(unique_new))

        if email_config[CONF_EMAIL_AUTO_ADD]:
            # Auto-add to tracked packages.
            packages = list(entry.options.get(CONF_PACKAGES, []))
            for p in unique_new:
                packages.append({
                    CONF_TRACKING_ID: p.tracking_id,
                    CONF_VENDOR: p.vendor,
                    CONF_NAME: p.tracking_id,
                })
            hass.config_entries.async_update_entry(
                entry, options={**entry.options, CONF_PACKAGES: packages}
            )
        else:
            # Add to discovered packages list for user confirmation.
            discovered = list(existing_discovered)
            for p in unique_new:
                discovered.append({
                    "tracking_id": p.tracking_id,
                    "vendor": p.vendor,
                    "source_subject": p.source_subject,
                    "source_sender": p.source_sender,
                    "discovered_at": datetime.now(UTC).isoformat(),
                })
            hass.config_entries.async_update_entry(
                entry, options={**entry.options, CONF_DISCOVERED_PACKAGES: discovered}
            )

    return unique_new


async def async_test_email_connection(
    server: str, port: int, username: str, password: str
) -> bool:
    """Test IMAP connection with given credentials."""
    client = EmailClient(
        server=server,
        port=port,
        username=username,
        password=password,
    )
    return await client.test_connection()
