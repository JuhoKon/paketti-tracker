## 1. Project Scaffold & Add-on Infrastructure

- [x] 1.1 Create `addon/` directory structure (app/, app/routers/, app/services/, app/scrapers/, app/email/, app/db/)
- [x] 1.2 Create `addon/config.yaml` (HA add-on manifest with ingress, options, arch, etc.)
- [x] 1.3 Create `addon/Dockerfile` (Python 3.12-slim, pip install, copy app, expose 8099)
- [x] 1.4 Create `addon/run.sh` entry point (exec uvicorn)
- [x] 1.5 Create `addon/requirements.txt` (fastapi, uvicorn, aiohttp, aiosqlite, aiomqtt, aioimaplib, pydantic)
- [x] 1.6 Create `repository.yaml` for HA add-on repository
- [x] 1.7 Create `addon/app/main.py` with FastAPI app, lifespan, static mount, and health endpoint
- [x] 1.8 Create `addon/app/config.py` with settings from environment variables
- [x] 1.9 Verify add-on loads: build Docker image locally, confirm health endpoint responds

## 2. Database Layer

- [x] 2.1 Create `addon/app/database.py` — async SQLite connection pool, init, close
- [x] 2.2 Create schema migration v1: packages, tracking_events, settings, discovered_packages tables
- [x] 2.3 Create `addon/app/db/repository.py` — PackageRepository with CRUD operations
- [x] 2.4 Create `addon/app/db/settings_repository.py` — key-value settings store (poll_interval, notifications, email config)
- [x] 2.5 Write tests for repository layer (test_repository.py)

## 3. Pydantic Models

- [x] 3.1 Create `addon/app/models.py` — request/response models (PackageCreate, PackageUpdate, PackageResponse, TrackingEvent, Settings, NotificationConfig, EmailConfig, DiscoveredPackage)
- [x] 3.2 Create `addon/app/db/models.py` — internal DB row models (dataclasses or TypedDicts)

## 4. Port Scrapers

- [x] 4.1 Port `addon/app/scrapers/base.py` — BaseScraper with standalone aiohttp.ClientSession
- [x] 4.2 Port `addon/app/scrapers/posti.py` — Posti GraphQL scraper (replace hass session with aiohttp)
- [x] 4.3 Create `addon/app/scrapers/factory.py` — get_scraper helper
- [x] 4.4 Write tests for Posti scraper (test_posti_scraper.py, reuse existing test patterns)

## 5. REST API — Packages

- [x] 5.1 Create `addon/app/routers/packages.py` — GET /api/packages (list all)
- [x] 5.2 Add POST /api/packages (add new package)
- [x] 5.3 Add PATCH /api/packages/{tracking_id} (edit name/vendor)
- [x] 5.4 Add DELETE /api/packages/{tracking_id} (remove)
- [x] 5.5 Add POST /api/packages/refresh (trigger immediate poll)
- [x] 5.6 Write tests for packages API (test_packages_api.py, using httpx AsyncClient)

## 6. REST API — Settings, Notifications, Email

- [x] 6.1 Create `addon/app/routers/settings.py` — GET/PATCH /api/settings
- [x] 6.2 Add GET/PATCH /api/notifications endpoints
- [x] 6.3 Create `addon/app/routers/email.py` — GET/PATCH /api/email, POST /api/email/test
- [x] 6.4 Add GET /api/email/discovered, POST confirm, DELETE dismiss
- [x] 6.5 Write tests for settings/notifications/email APIs (test_settings_api.py)

## 7. Scheduler Service

- [x] 7.1 Create `addon/app/services/scraper_service.py` — polling loop with asyncio, skip delivered, error isolation
- [x] 7.2 Integrate scraper service with database (save results, update package status/events)
- [x] 7.3 Create `addon/app/services/notification_checker.py` — compare old/new status, match triggers
- [x] 7.4 Wire scraper_service → notification_checker → notify_service on each poll
- [x] 7.5 Write tests for scraper service and notification checker (test_scraper_service.py)

## 8. Email Service

- [x] 8.1 Port `addon/app/email/client.py` — IMAP client (standalone, no HA)
- [x] 8.2 Port `addon/app/email/parser.py` — regex extraction (direct copy with minor cleanup)
- [x] 8.3 Create `addon/app/services/email_service.py` — polling loop, deduplication, auto-add or queue
- [x] 8.4 Write tests for email service (test_email_service.py)

## 9. MQTT Sensor Publishing

- [x] 9.1 Create `addon/app/services/mqtt_service.py` — connect to broker, publish discovery config per package
- [x] 9.2 Implement state/attribute publishing on package update
- [x] 9.3 Implement availability (online on connect, offline on disconnect/shutdown)
- [x] 9.4 Implement sensor removal on package delete (publish empty config)
- [x] 9.5 Implement reconnect with full republish
- [x] 9.6 Write tests for MQTT service (test_mqtt_service.py, mock aiomqtt)

## 10. HA Notify Client

- [x] 10.1 Create `addon/app/services/notify_service.py` — call HA REST API with SUPERVISOR_TOKEN
- [x] 10.2 Integrate with notification_checker (fire on trigger match)
- [x] 10.3 Write tests for notify service (test_notify_service.py)

## 11. Frontend Port

- [x] 11.1 Create `addon/frontend/` with package.json, vite.config.ts, tsconfig
- [x] 11.2 Port `types.ts` (same interfaces)
- [x] 11.3 Rewrite `api.ts` — replace WS calls with fetch/REST calls
- [x] 11.4 Port App.tsx with React Router (/ dashboard, /settings page)
- [x] 11.5 Port PackageList, PackageCard, DeliveryTimeline, AddPackageDialog, EditPackageDialog
- [x] 11.6 Port SettingsDrawer → Settings page (NotificationSettings, EmailSettings sections)
- [x] 11.7 Port DiscoveredPackages component
- [x] 11.8 Update styles for standalone SPA (remove HA CSS variable dependencies, use own theme)
- [x] 11.9 Configure Vite build output to `addon/frontend/dist/`
- [x] 11.10 Mount static files in FastAPI (`app.mount("/", StaticFiles(...))`)

## 12. Integration & Finalization

- [x] 12.1 Wire all services into FastAPI lifespan (start scheduler, mqtt on startup; stop on shutdown)
- [x] 12.2 Handle ingress path prefix (X-Ingress-Path header, React Router basename)
- [x] 12.3 End-to-end test: build Docker, start, verify health, add package via API, check MQTT
- [x] 12.4 Remove old `custom_components/paketti_tracker/` directory
- [x] 12.5 Update root README with add-on installation instructions
- [x] 12.6 Run full test suite (ruff, mypy, pytest) and fix issues
