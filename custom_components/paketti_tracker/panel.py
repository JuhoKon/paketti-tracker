"""Panel registration for Paketti Tracker."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

PANEL_URL = "/paketti_tracker_panel"
PANEL_FRONTEND_DIR = Path(__file__).parent / "frontend" / "dist"
PANEL_FILENAME = "paketti-tracker-panel.js"


async def async_register_panel(hass: HomeAssistant) -> None:
    """Register the Paketti Tracker sidebar panel."""
    # Register the static path so HA can serve the JS file.
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                url_path=PANEL_URL,
                path=str(PANEL_FRONTEND_DIR),
                cache_headers=True,
            )
        ]
    )

    # Register the panel in the sidebar.
    async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title="Paketti Tracker",
        sidebar_icon="mdi:package-variant",
        frontend_url_path="paketti-tracker",
        require_admin=False,
        config={
            "_panel_custom": {
                "name": "paketti-tracker-panel",
                "embed_iframe": False,
                "trust_external": False,
                "js_url": f"{PANEL_URL}/{PANEL_FILENAME}",
            }
        },
    )


async def async_unregister_panel(hass: HomeAssistant) -> None:
    """Remove the panel from the sidebar."""
    from homeassistant.components.frontend import async_remove_panel

    async_remove_panel(hass, "paketti-tracker")
