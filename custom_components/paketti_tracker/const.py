"""Constants for the Paketti Tracker integration."""

DOMAIN = "paketti_tracker"

# Vendor identifiers
VENDOR_POSTI = "posti"
VENDOR_POSTNORD = "postnord"
VENDOR_MATKAHUOLTO = "matkahuolto"

VENDORS = [VENDOR_POSTI, VENDOR_POSTNORD, VENDOR_MATKAHUOLTO]

VENDOR_NAMES: dict[str, str] = {
    VENDOR_POSTI: "Posti",
    VENDOR_POSTNORD: "Postnord",
    VENDOR_MATKAHUOLTO: "Matkahuolto",
}

# Normalized status vocabulary (ADR-003)
STATUS_PENDING = "pending"
STATUS_IN_TRANSIT = "in_transit"
STATUS_OUT_FOR_DELIVERY = "out_for_delivery"
STATUS_DELIVERED = "delivered"
STATUS_EXCEPTION = "exception"
STATUS_UNKNOWN = "unknown"

ALL_STATUSES = [
    STATUS_PENDING,
    STATUS_IN_TRANSIT,
    STATUS_OUT_FOR_DELIVERY,
    STATUS_DELIVERED,
    STATUS_EXCEPTION,
    STATUS_UNKNOWN,
]

# Config / options keys
CONF_PACKAGES = "packages"
CONF_TRACKING_ID = "tracking_id"
CONF_VENDOR = "vendor"
CONF_NAME = "name"

# Options flow actions
ACTION_ADD = "add"
ACTION_REMOVE = "remove"

# Coordinator
SCAN_INTERVAL_MINUTES = 60

# Sensor attribute keys
ATTR_VENDOR = "vendor"
ATTR_TRACKING_ID = "tracking_id"
ATTR_PACKAGE_NAME = "name"
ATTR_ESTIMATED_DELIVERY = "estimated_delivery"
ATTR_LAST_LOCATION = "last_location"
ATTR_LAST_EVENT_TIME = "last_event_time"
ATTR_EVENTS = "events"
ATTR_DELIVERED = "delivered"

# Max events stored in attributes
MAX_EVENTS = 10
