## Why

Home Assistant is already the hub for home automation, but there is no native way to track postal packages from Finnish and Nordic carriers inside it. Tracking links require opening browser tabs to multiple vendor sites; there is no single place to see all packages at a glance or trigger automations when a package status changes.

## What Changes

- New HACS-compatible custom integration `paketti_tracker` added to HA
- Users can add and remove tracked packages (tracking ID + vendor + optional name) via the integration's options flow, no YAML required
- One `SensorEntity` is created per tracked package, exposing a normalized status as state and full event history as attributes
- A `DataUpdateCoordinator` polls three carrier scrapers (Posti, Postnord, Matkahuolto) hourly; polling stops automatically once a package is marked delivered
- Delivered packages persist as entities until the user manually removes them

## Capabilities

### New Capabilities

- `package-tracking`: Core tracking capability — scraping carrier websites, normalizing results into a vendor-agnostic status model, and exposing data as HA sensor entities
- `package-management`: Adding and removing tracked packages via the HA options flow (config entry UI)
- `carrier-scrapers`: Per-vendor scraper implementations for Posti, Postnord, and Matkahuolto

### Modified Capabilities

_(none — this is the initial integration)_

## Impact

- New `custom_components/paketti_tracker/` directory
- Runtime dependencies: `httpx` (async HTTP), `beautifulsoup4` (HTML parsing fallback); declared in `manifest.json`
- No external API keys or credentials required
- HA minimum version to be confirmed against `DataUpdateCoordinator` and `OptionsFlow` APIs in use
- Entity platform: `sensor` only

## Non-goals

- UPS support (deferred — their tracking page is JavaScript-heavy and requires significant reverse-engineering effort)
- Push notifications (HA automations handle this using the sensor state)
- A custom Lovelace card
- Multi-user or shared tracking (single HA instance, personal use)
- Automatic email parsing to add packages
