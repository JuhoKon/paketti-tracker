"""Tests for config flow and options flow."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from custom_components.paketti_tracker.config_flow import (
    PakettiConfigFlow,
    PakettiOptionsFlow,
)
from custom_components.paketti_tracker.const import (
    CONF_NAME,
    CONF_PACKAGES,
    CONF_TRACKING_ID,
    CONF_VENDOR,
    VENDOR_POSTI,
)

# -- Config Flow Tests --------------------------------------------------------


@pytest.mark.asyncio
async def test_config_flow_creates_entry():
    """Test that the config flow creates an entry on user confirmation."""
    flow = PakettiConfigFlow()
    flow.hass = MagicMock()
    flow.hass.config_entries = MagicMock()
    flow.hass.config_entries.async_entries = MagicMock(return_value=[])

    # Mock the unique_id methods
    flow.context = {"source": "user"}
    flow._async_current_entries = MagicMock(return_value=[])

    with (
        patch.object(flow, "async_set_unique_id", return_value=None),
        patch.object(flow, "_abort_if_unique_id_configured"),
    ):
        # First call: show form
        result = await flow.async_step_user(user_input=None)
        assert result["type"] == "form"
        assert result["step_id"] == "user"

        # Second call: create entry
        result = await flow.async_step_user(user_input={})
        assert result["type"] == "create_entry"
        assert result["title"] == "Paketti Tracker"
        assert result["options"] == {CONF_PACKAGES: []}


# -- Options Flow Tests -------------------------------------------------------


def _make_options_flow(packages: list[dict]) -> PakettiOptionsFlow:
    """Create an options flow with given packages."""
    entry = MagicMock()
    entry.options = {CONF_PACKAGES: packages}
    entry.entry_id = "test_entry"

    flow = PakettiOptionsFlow(entry)
    flow.hass = MagicMock()
    return flow


@pytest.mark.asyncio
async def test_options_flow_init_shows_actions():
    """Test that init step shows add (and remove if packages exist)."""
    flow = _make_options_flow(
        [{CONF_TRACKING_ID: "PKG1", CONF_VENDOR: VENDOR_POSTI, CONF_NAME: "My Package"}]
    )

    result = await flow.async_step_init(user_input=None)
    assert result["type"] == "form"
    assert result["step_id"] == "init"


@pytest.mark.asyncio
async def test_options_flow_add_package():
    """Test adding a package via options flow."""
    flow = _make_options_flow([])

    result = await flow.async_step_add(
        user_input={
            CONF_TRACKING_ID: "JJFI123456",
            CONF_VENDOR: VENDOR_POSTI,
            CONF_NAME: "Test Package",
        }
    )

    assert result["type"] == "create_entry"
    packages = result["data"][CONF_PACKAGES]
    assert len(packages) == 1
    assert packages[0][CONF_TRACKING_ID] == "JJFI123456"
    assert packages[0][CONF_VENDOR] == VENDOR_POSTI
    assert packages[0][CONF_NAME] == "Test Package"


@pytest.mark.asyncio
async def test_options_flow_add_normalizes_tracking_id():
    """Test that tracking ID is uppercased and trimmed."""
    flow = _make_options_flow([])

    result = await flow.async_step_add(
        user_input={
            CONF_TRACKING_ID: "  jjfi123456  ",
            CONF_VENDOR: VENDOR_POSTI,
            CONF_NAME: "",
        }
    )

    assert result["type"] == "create_entry"
    packages = result["data"][CONF_PACKAGES]
    assert packages[0][CONF_TRACKING_ID] == "JJFI123456"
    # Empty name defaults to tracking ID.
    assert packages[0][CONF_NAME] == "JJFI123456"


@pytest.mark.asyncio
async def test_options_flow_add_duplicate_shows_error():
    """Test that duplicate tracking ID shows error."""
    flow = _make_options_flow(
        [{CONF_TRACKING_ID: "JJFI123456", CONF_VENDOR: VENDOR_POSTI, CONF_NAME: "Existing"}]
    )

    result = await flow.async_step_add(
        user_input={
            CONF_TRACKING_ID: "jjfi123456",
            CONF_VENDOR: VENDOR_POSTI,
            CONF_NAME: "Duplicate",
        }
    )

    assert result["type"] == "form"
    assert result["errors"][CONF_TRACKING_ID] == "already_tracked"


@pytest.mark.asyncio
async def test_options_flow_add_empty_shows_error():
    """Test that empty tracking ID shows error."""
    flow = _make_options_flow([])

    result = await flow.async_step_add(
        user_input={
            CONF_TRACKING_ID: "   ",
            CONF_VENDOR: VENDOR_POSTI,
            CONF_NAME: "",
        }
    )

    assert result["type"] == "form"
    assert result["errors"][CONF_TRACKING_ID] == "empty_tracking_id"


@pytest.mark.asyncio
async def test_options_flow_remove_package():
    """Test removing packages via options flow."""
    flow = _make_options_flow(
        [
            {CONF_TRACKING_ID: "PKG1", CONF_VENDOR: VENDOR_POSTI, CONF_NAME: "Package 1"},
            {CONF_TRACKING_ID: "PKG2", CONF_VENDOR: VENDOR_POSTI, CONF_NAME: "Package 2"},
        ]
    )

    result = await flow.async_step_remove(
        user_input={
            "remove": ["PKG1"],
        }
    )

    assert result["type"] == "create_entry"
    packages = result["data"][CONF_PACKAGES]
    assert len(packages) == 1
    assert packages[0][CONF_TRACKING_ID] == "PKG2"


@pytest.mark.asyncio
async def test_options_flow_remove_no_packages_aborts():
    """Test that remove with no packages aborts."""
    flow = _make_options_flow([])

    result = await flow.async_step_remove(user_input=None)
    assert result["type"] == "abort"
    assert result["reason"] == "no_packages"
