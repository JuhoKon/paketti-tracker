# Paketti Tracker

Home Assistant Supervisor add-on for tracking Finnish postal packages. Currently supports **Posti** (Postnord and Matkahuolto planned for future).

## Architecture

- **Backend:** FastAPI (Python 3.12, uvicorn) serving REST API
- **Frontend:** React SPA served via HA ingress proxy
- **Sensors:** MQTT discovery (requires Mosquitto add-on)
- **Storage:** SQLite (persisted to `/data/`)
- **Notifications:** HA REST API (mobile app push via SUPERVISOR_TOKEN)

## Features

- Track multiple packages with Posti carrier support
- MQTT sensors with HA auto-discovery (one sensor per package)
- React UI accessible via HA sidebar (ingress)
- Background polling every 60 minutes (configurable)
- Email parsing for automatic package discovery (IMAP)
- Push notifications on status changes (delivered, in transit)
- No API keys required — uses Posti's anonymous GraphQL API

### Sensor States

| State | Meaning |
|-------|---------|
| `pending` | Order received, not yet in carrier's system |
| `in_transit` | Package is being transported |
| `out_for_delivery` | Package is out for delivery |
| `delivered` | Package delivered or ready for pickup |
| `exception` | Problem with delivery (returned, damaged) |
| `unknown` | Unrecognized status |

## Installation

### Prerequisites

- Home Assistant OS with Supervisor
- Mosquitto add-on (for MQTT sensors)

### Add-on Installation

1. Add this repository URL to your HA add-on store: Settings → Add-ons → Add-on Store → ⋮ → Repositories
2. Install "Paketti Tracker"
3. Start the add-on
4. Open the Web UI (appears in sidebar)

## Configuration

Add-on options in `config.yaml`:

| Option | Default | Description |
|--------|---------|-------------|
| `poll_interval_minutes` | 60 | How often to check for package updates |
| `email_poll_interval_minutes` | 30 | How often to check email for tracking IDs |
| `log_level` | info | Logging verbosity (debug/info/warning/error) |

Additional settings (notification triggers, email IMAP config) are managed via the web UI Settings page.

## API

The add-on exposes a REST API at port 8099 (accessed via ingress):

- `GET /api/health` — Health check
- `GET /api/packages` — List all packages
- `POST /api/packages` — Add a package
- `PATCH /api/packages/{id}` — Edit a package
- `DELETE /api/packages/{id}` — Remove a package
- `POST /api/packages/refresh` — Trigger immediate poll
- `GET/PATCH /api/settings` — General settings
- `GET/PATCH /api/notifications` — Notification config
- `GET/PATCH /api/email` — Email IMAP config
- `GET /api/email/discovered` — Packages found in email

## Development

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
pip install fastapi uvicorn aiosqlite pydantic pydantic-settings httpx asgi-lifespan pytest-asyncio aiohttp

# Run tests
pytest tests/addon/ -v

# Frontend development
cd addon/frontend
npm install
npm run dev    # Dev server with API proxy to localhost:8099
npm run build  # Production build to dist/
```

### Running locally

```bash
cd addon
PAKETTI_DATA_DIR=/tmp/paketti_dev uvicorn app.main:app --host 0.0.0.0 --port 8099 --reload
```

## License

MIT
