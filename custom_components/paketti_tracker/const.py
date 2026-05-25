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
DEFAULT_POLL_INTERVAL_MINUTES = 60
CONF_POLL_INTERVAL = "poll_interval_minutes"

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

# Notification configuration
CONF_NOTIFICATIONS = "notifications"
CONF_NOTIFICATIONS_ENABLED = "enabled"
CONF_NOTIFICATIONS_TRIGGERS = "triggers"
CONF_NOTIFICATIONS_DEVICES = "devices"

# Default notification triggers (status transitions that fire a notification)
DEFAULT_NOTIFICATION_TRIGGERS: list[str] = [
    STATUS_IN_TRANSIT,
    STATUS_OUT_FOR_DELIVERY,
    STATUS_DELIVERED,
    STATUS_EXCEPTION,
]

# Email configuration
CONF_EMAIL = "email"
CONF_EMAIL_ENABLED = "enabled"
CONF_EMAIL_IMAP_SERVER = "imap_server"
CONF_EMAIL_IMAP_PORT = "imap_port"
CONF_EMAIL_USERNAME = "username"
CONF_EMAIL_PASSWORD = "password"
CONF_EMAIL_FOLDER = "folder"
CONF_EMAIL_POLL_INTERVAL = "poll_interval_minutes"
CONF_EMAIL_AUTO_ADD = "auto_add"
CONF_EMAIL_SEARCH_DAYS = "search_days"

DEFAULT_EMAIL_IMAP_PORT = 993
DEFAULT_EMAIL_FOLDER = "INBOX"
DEFAULT_EMAIL_POLL_INTERVAL_MINUTES = 30
DEFAULT_EMAIL_SEARCH_DAYS = 7

# Discovered packages (from email parsing)
CONF_DISCOVERED_PACKAGES = "discovered_packages"

# Carrier tracking URL templates ({tracking_id} is replaced at runtime)
TRACKING_URL_TEMPLATES: dict[str, str] = {
    VENDOR_POSTI: "https://www.posti.fi/fi/seuranta#/lahetys/{tracking_id}",
    VENDOR_POSTNORD: "https://tracking.postnord.com/fi/?id={tracking_id}",
    VENDOR_MATKAHUOLTO: "https://www.matkahuolto.fi/seuranta/tilaus/{tracking_id}",
}


def get_tracking_url(vendor: str, tracking_id: str) -> str | None:
    """Get the public tracking page URL for a package."""
    template = TRACKING_URL_TEMPLATES.get(vendor)
    if template is None:
        return None
    return template.format(tracking_id=tracking_id)
