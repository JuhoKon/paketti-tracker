## Context

Paketti Tracker currently runs as a Home Assistant custom integration (`custom_components/paketti_tracker/`). It tracks Finnish postal packages via Posti's anonymous GraphQL API, parses emails for tracking IDs, sends notifications on status changes, and provides a React-based sidebar panel UI.

The target deployment is HA OS with Supervisor. The rewrite moves everything into a Docker-based add-on with FastAPI serving both the REST API and static React frontend via HA's ingress proxy. Package sensors are published to HA via MQTT discovery (Mosquitto add-on required).

**Current state:** Working integration with 92 tests, Posti scraper, email parsing, notifications, and frontend panel. All code is proven but architecturally coupled to HA internals.

## Goals / Non-Goals

**Goals:**
- Standalone FastAPI add-on serving REST API + React SPA via ingress
- SQLite persistence for packages, events, config, and discovered packages
- MQTT discovery for sensor entities in HA (one sensor per package)
- Background polling for scrapers and email on configurable intervals
- Notifications via HA's REST API (calling notify services)
- Port all existing functionality with minimal behavior changes
- Standard pytest testing without HA mocking

**Non-Goals:**
- Multi-user support or external authentication
- Postnord/Matkahuolto scraper implementation
- Data migration from old integration
- Real-time WebSocket push to frontend (polling/refresh is fine)
- Running outside HA OS (no standalone Docker Compose support)

## Decisions

### D1: FastAPI as application framework

**Choice:** FastAPI with uvicorn (single worker, asyncio)

**Alternatives considered:**
- Flask: Sync-first, would need gevent/threading for async scrapers
- aiohttp server: Lower-level, less developer ergonomics (no Pydantic validation, no OpenAPI)
- Litestar: Good but less ecosystem/community than FastAPI

**Rationale:** FastAPI is async-native, has built-in request validation via Pydantic, auto-generates OpenAPI docs, and has a large ecosystem. Single uvicorn worker with asyncio is sufficient for single-user workload.

### D2: SQLite via aiosqlite

**Choice:** aiosqlite with raw SQL (no ORM)

**Alternatives considered:**
- SQLAlchemy async: Overkill for 4-5 tables, adds complexity
- TinyDB/JSON file: No query capability, no schema enforcement

**Rationale:** Simple schema (packages, events, config, discovered_packages). Raw SQL is readable and testable. aiosqlite provides async interface. Schema versioning via a `schema_version` table with sequential migration scripts.

### D3: MQTT discovery for HA sensors

**Choice:** aiomqtt client publishing HA MQTT discovery messages

**Alternatives considered:**
- HA REST API with `states` endpoint: Can set entity states but doesn't create proper entities with device registry
- Companion integration: Best entity control but two things to install

**Rationale:** MQTT discovery is the standard HA pattern for external devices/services. Sensors auto-appear with proper device grouping, availability, and state class. Requires Mosquitto add-on (common on HA OS). The add-on config will reference the MQTT broker connection.

**Sensor design:**
- Device: `paketti_tracker` (one device for all sensors)
- Entity per package: `sensor.paketti_<tracking_id_lower>`
- State: normalized status string
- Attributes: vendor, name, last_location, last_event_time, last_updated, tracking_url, delivered

### D4: Ingress for UI access

**Choice:** FastAPI serves static React build at `/` with HA ingress proxy

**Alternatives considered:**
- Separate nginx container: Unnecessary complexity for serving static files
- Direct port exposure: Bypasses HA auth

**Rationale:** HA ingress provides authentication, SSL, and sidebar integration automatically. FastAPI's `StaticFiles` mount serves the built React app. API routes under `/api/`. Ingress token passed via `X-Ingress-Path` header for URL rewriting.

### D5: Background scheduling with asyncio tasks

**Choice:** asyncio background tasks managed by app lifespan

**Alternatives considered:**
- APScheduler: Dependency for something asyncio handles natively
- Celery: Requires broker, massive overkill

**Rationale:** Two periodic tasks (scraper poll every 60min, email poll every 30min). `asyncio.create_task` with `asyncio.sleep` loops is the simplest solution. Managed via FastAPI's lifespan context manager for clean startup/shutdown.

### D6: HA REST API for notifications

**Choice:** Call HA's REST API (`/api/services/notify/<device>`) using Supervisor token

**Alternatives considered:**
- ntfy.sh: Extra service, user needs separate app
- Direct push notification: Would need Firebase/APNs integration

**Rationale:** The Supervisor provides a `SUPERVISOR_TOKEN` environment variable that grants access to HA's REST API. Calling notify services keeps notifications unified in HA's existing mobile app setup. No extra configuration needed from the user.

### D7: Project structure

```
paketti-tracker/
├── addon/
│   ├── Dockerfile
│   ├── config.yaml          # HA add-on manifest
│   ├── run.sh               # Entry point
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py          # FastAPI app + lifespan
│   │   ├── config.py        # Settings (from env + SQLite)
│   │   ├── database.py      # SQLite setup, migrations
│   │   ├── models.py        # Pydantic models (request/response)
│   │   ├── routers/
│   │   │   ├── packages.py  # CRUD: /api/packages
│   │   │   ├── settings.py  # /api/settings, /api/notifications, /api/email
│   │   │   └── email.py     # /api/email/discovered, confirm, dismiss, test
│   │   ├── services/
│   │   │   ├── scraper_service.py   # Polling loop + scraper orchestration
│   │   │   ├── email_service.py     # Email polling loop
│   │   │   ├── mqtt_service.py      # MQTT discovery + state publishing
│   │   │   ├── notify_service.py    # HA REST API notify calls
│   │   │   └── notification_checker.py  # Status change → trigger matching
│   │   ├── scrapers/
│   │   │   ├── base.py      # BaseScraper (ported)
│   │   │   ├── posti.py     # Posti scraper (ported)
│   │   │   └── factory.py
│   │   ├── email/
│   │   │   ├── client.py    # IMAP client (ported)
│   │   │   └── parser.py    # Regex extraction (ported)
│   │   └── db/
│   │       ├── repository.py    # Data access layer
│   │       └── migrations/      # SQL migration files
│   └── frontend/
│       ├── package.json
│       ├── vite.config.ts
│       ├── src/
│       │   ├── App.tsx
│       │   ├── api.ts        # REST client (replaces WS)
│       │   ├── types.ts
│       │   └── components/   # Ported + enhanced
│       └── dist/             # Built SPA (served by FastAPI)
├── tests/
│   ├── conftest.py
│   ├── test_packages_api.py
│   ├── test_scraper_service.py
│   ├── test_mqtt_service.py
│   ├── test_email_service.py
│   └── test_notify_service.py
├── repository.yaml           # HA add-on repository manifest
└── README.md
```

## Risks / Trade-offs

**[Risk] Mosquitto add-on required** → Document as prerequisite. Most HA OS users already have it for Zigbee2MQTT or other integrations. If not installed, sensors won't appear but tracker still works via UI.

**[Risk] Ingress path handling** → HA ingress rewrites URLs. React Router needs `basename` set to the ingress path. FastAPI must handle `X-Ingress-Path` header. Well-documented pattern in HA add-on community.

**[Risk] Supervisor token permissions** → The `SUPERVISOR_TOKEN` has broad access. We only use it for notify service calls and MQTT broker discovery. Document the scope.

**[Risk] SQLite in Docker** → Data lives in `/data/` (mapped to HA's add-on data directory). Survives container restarts and updates. No backup automation — user must back up HA normally.

**[Risk] Losing existing tracked packages** → No migration path. Users must re-add packages. Acceptable for a single-user project in early development.

**[Trade-off] No real-time updates** → Frontend polls API on interval or user-triggered refresh. Acceptable for package tracking (events change hourly at most). Could add SSE later if needed.

## Open Questions

- Should the old `custom_components/` code be removed in this change or kept alongside for reference?
- Exact MQTT topic structure: `homeassistant/sensor/paketti_tracker/<id>/config` (standard HA discovery) — confirm this works with the default Mosquitto setup.
