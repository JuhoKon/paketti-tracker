# Paketti Tracker

Home Assistant custom integration for tracking Finnish postal packages. Currently supports **Posti** (Postnord and Matkahuolto planned for future).

## Features

- Track multiple packages from a single integration instance
- One sensor entity per package with normalized status states
- Automatic polling every 60 minutes (stops polling delivered packages)
- No API keys or credentials required — uses anonymous access
- Options flow for adding/removing packages without reconfiguration

### Sensor States

| State | Meaning |
|-------|---------|
| `pending` | Order received, not yet in Posti's system |
| `in_transit` | Package is being transported |
| `out_for_delivery` | Package is out for delivery |
| `delivered` | Package delivered or ready for pickup |
| `exception` | Problem with delivery (returned, damaged) |
| `unknown` | Unrecognized status |

### Sensor Attributes

Each sensor entity exposes:
- `tracking_id` — the tracking code
- `vendor` — carrier name (e.g. "Posti")
- `name` — user-provided package name
- `delivered` — boolean
- `estimated_delivery` — estimated delivery date (if available)
- `last_location` — city of most recent event
- `last_event_time` — timestamp of most recent event
- `events` — list of up to 10 tracking events (timestamp, description, location)

## Installation

### HACS (recommended)

1. Add this repository as a custom repository in HACS
2. Search for "Paketti Tracker" and install
3. Restart Home Assistant

### Manual

1. Copy `custom_components/paketti_tracker/` to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for "Paketti Tracker" and add it
3. To add packages: go to the integration options (click Configure)
4. Select "Add package", enter tracking ID, choose carrier, optionally name it

## Development

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check custom_components/ tests/

# Format
ruff format custom_components/ tests/

# Type check
mypy custom_components/
```

## License

MIT
