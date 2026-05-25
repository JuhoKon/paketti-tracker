"""Tests for PakettiSensor."""

from __future__ import annotations

from datetime import UTC, date, datetime
from unittest.mock import MagicMock

from custom_components.paketti_tracker.const import (
    ATTR_DELIVERED,
    ATTR_ESTIMATED_DELIVERY,
    ATTR_EVENTS,
    ATTR_LAST_EVENT_TIME,
    ATTR_LAST_LOCATION,
    ATTR_PACKAGE_NAME,
    ATTR_TRACKING_ID,
    ATTR_VENDOR,
    DOMAIN,
    MAX_EVENTS,
    STATUS_DELIVERED,
    STATUS_IN_TRANSIT,
    VENDOR_POSTI,
)
from custom_components.paketti_tracker.models import TrackingEvent, TrackingResult
from custom_components.paketti_tracker.sensor import PakettiSensor


def _make_result(
    tracking_id: str = "PKG1",
    status: str = STATUS_IN_TRANSIT,
    delivered: bool = False,
    num_events: int = 3,
) -> TrackingResult:
    """Create a test TrackingResult."""
    events = [
        TrackingEvent(
            timestamp=datetime(2026, 5, 22, 10, i, 0, tzinfo=UTC),
            description=f"Event {i}",
            location=f"CITY_{i}",
        )
        for i in range(num_events)
    ]
    return TrackingResult(
        tracking_id=tracking_id,
        vendor=VENDOR_POSTI,
        status=status,
        delivered=delivered,
        events=events,
        estimated_delivery=date(2026, 5, 24),
        last_location="CITY_0" if events else None,
        last_event_time=events[0].timestamp if events else None,
    )


def _make_coordinator(data: dict[str, TrackingResult] | None = None) -> MagicMock:
    """Create a mock coordinator."""
    coordinator = MagicMock()
    coordinator.data = data
    coordinator.last_update_success = True
    return coordinator


def _make_sensor(
    coordinator: MagicMock,
    tracking_id: str = "PKG1",
    package_name: str = "My Package",
) -> PakettiSensor:
    """Create a sensor instance."""
    sensor = PakettiSensor(
        coordinator=coordinator,
        tracking_id=tracking_id,
        vendor=VENDOR_POSTI,
        package_name=package_name,
    )
    return sensor


class TestPakettiSensor:
    """Tests for PakettiSensor entity."""

    def test_native_value_returns_status(self):
        """Test that native_value returns the normalized status."""
        result = _make_result(status=STATUS_IN_TRANSIT)
        coordinator = _make_coordinator({"PKG1": result})
        sensor = _make_sensor(coordinator)

        assert sensor.native_value == STATUS_IN_TRANSIT

    def test_native_value_delivered(self):
        """Test delivered status."""
        result = _make_result(status=STATUS_DELIVERED, delivered=True)
        coordinator = _make_coordinator({"PKG1": result})
        sensor = _make_sensor(coordinator)

        assert sensor.native_value == STATUS_DELIVERED

    def test_native_value_none_when_no_data(self):
        """Test that native_value is None when coordinator has no data for package."""
        coordinator = _make_coordinator({})
        sensor = _make_sensor(coordinator)

        assert sensor.native_value is None

    def test_available_true_when_data_exists(self):
        """Test available when data exists."""
        result = _make_result()
        coordinator = _make_coordinator({"PKG1": result})
        sensor = _make_sensor(coordinator)

        assert sensor.available is True

    def test_available_false_when_no_data(self):
        """Test unavailable when no data for this package."""
        coordinator = _make_coordinator({})
        sensor = _make_sensor(coordinator)

        assert sensor.available is False

    def test_available_false_when_coordinator_failed(self):
        """Test unavailable when coordinator update failed."""
        result = _make_result()
        coordinator = _make_coordinator({"PKG1": result})
        coordinator.last_update_success = False
        sensor = _make_sensor(coordinator)

        assert sensor.available is False

    def test_available_false_when_data_is_none(self):
        """Test unavailable when coordinator data is None."""
        coordinator = _make_coordinator(None)
        sensor = _make_sensor(coordinator)

        assert sensor.available is False

    def test_extra_state_attributes(self):
        """Test that extra_state_attributes contains expected fields."""
        result = _make_result()
        coordinator = _make_coordinator({"PKG1": result})
        sensor = _make_sensor(coordinator, package_name="My Package")

        attrs = sensor.extra_state_attributes

        assert attrs[ATTR_TRACKING_ID] == "PKG1"
        assert attrs[ATTR_VENDOR] == "Posti"
        assert attrs[ATTR_PACKAGE_NAME] == "My Package"
        assert attrs[ATTR_DELIVERED] is False
        assert attrs[ATTR_ESTIMATED_DELIVERY] == "2026-05-24"
        assert attrs[ATTR_LAST_LOCATION] == "CITY_0"
        assert ATTR_LAST_EVENT_TIME in attrs
        assert ATTR_EVENTS in attrs
        assert len(attrs[ATTR_EVENTS]) == 3

    def test_extra_state_attributes_empty_when_no_data(self):
        """Test that attributes are empty when no data."""
        coordinator = _make_coordinator({})
        sensor = _make_sensor(coordinator)

        assert sensor.extra_state_attributes == {}

    def test_events_capped_at_max(self):
        """Test that events are capped at MAX_EVENTS."""
        result = _make_result(num_events=MAX_EVENTS + 5)
        coordinator = _make_coordinator({"PKG1": result})
        sensor = _make_sensor(coordinator)

        attrs = sensor.extra_state_attributes
        assert len(attrs[ATTR_EVENTS]) == MAX_EVENTS

    def test_unique_id(self):
        """Test unique_id format."""
        coordinator = _make_coordinator({})
        sensor = _make_sensor(coordinator, tracking_id="JJFI123")

        assert sensor.unique_id == f"{DOMAIN}_JJFI123"

    def test_icon(self):
        """Test default icon."""
        coordinator = _make_coordinator({})
        sensor = _make_sensor(coordinator)

        assert sensor.icon == "mdi:package-variant"
