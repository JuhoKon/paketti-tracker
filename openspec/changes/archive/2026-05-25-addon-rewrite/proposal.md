## Why

The current implementation is a HACS custom integration that runs inside Home Assistant's Python process. This creates architectural friction: the React panel fights HA's panel constraints (IIFE bundle, no routing, JS committed to repo), IMAP email polling doesn't belong in HA's event loop, and testing requires extensive HA mocking. Since the target environment is HA OS, rewriting as a Supervisor add-on gives us a proper web server with ingress, isolated dependencies in Docker, own SQLite database, and standard Python testing — while still providing HA sensor entities via MQTT discovery.

## What Changes

- **BREAKING**: Remove the entire `custom_components/paketti_tracker/` integration
- **BREAKING**: Remove HACS compatibility artifacts (`hacs.json`, manifest, config_flow)
- New: HA Supervisor add-on with Docker container (Python 3.12 + FastAPI + uvicorn)
- New: REST API replacing WebSocket commands (same functionality, standard HTTP)
- New: SQLite database for packages, events, config, and discovered packages
- New: MQTT sensor publishing via HA MQTT discovery protocol
- New: Ingress-compatible web UI (React SPA served by FastAPI)
- New: Background scheduler for scraper polling and email polling (asyncio tasks)
- New: HA REST API client for triggering notify services
- Port: Posti scraper, email client, email parser, notification logic (minimal changes)
- Port: React frontend components (adapt from WS calls to REST API)

## Non-goals

- Postnord/Matkahuolto scraper implementation (deferred, interfaces stay)
- Multi-user / authentication (single-user, protected by HA ingress auth)
- External access without HA (ingress only)
- Migration tool from old integration data

## Capabilities

### New Capabilities
- `addon-infrastructure`: Supervisor add-on config, Dockerfile, ingress setup, health checks
- `rest-api`: FastAPI REST endpoints replacing WS commands (packages CRUD, settings, email, notifications)
- `database`: SQLite schema, repository layer, migrations
- `mqtt-sensors`: MQTT discovery publishing, sensor state updates, availability
- `scheduler`: Background task scheduling for scraper polling and email polling
- `ha-notify-client`: HA REST API client for calling notify services from the add-on

### Modified Capabilities
- `carrier-scrapers`: No requirement change, but implementation moves from HA session to standalone aiohttp
- `email-parsing`: No requirement change, moves to standalone module
- `frontend-panel`: **BREAKING** — changes from HA panel (WS API) to ingress SPA (REST API)
- `notifications`: Changes from direct HA service call to HA REST API call

## Impact

- **Code**: Entire `custom_components/` directory removed; new `addon/` directory with FastAPI app
- **Frontend**: React components ported; `api.ts` changes from WS to REST; gains proper routing
- **Dependencies**: Adds FastAPI, uvicorn, aiomqtt, aiosqlite; removes homeassistant dependency
- **Distribution**: Changes from HACS GitHub release to HA add-on repository
- **Testing**: Standard pytest (no HA mocking); httpx test client for API tests
- **Users**: Must uninstall old integration, install add-on, re-add packages (no migration)
