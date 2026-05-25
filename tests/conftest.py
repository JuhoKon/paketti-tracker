"""Shared test fixtures and configuration."""

from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def patch_ha_frame_helper():
    """Patch HA's frame helper so tests can instantiate HA classes directly."""
    with patch(
        "homeassistant.helpers.frame.report_usage",
        return_value=None,
    ):
        yield
