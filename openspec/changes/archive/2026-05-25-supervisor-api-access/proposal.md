## Why

The add-on fails to connect to MQTT and may fail to scrape Posti packages when deployed on HA OS. Two root causes:

1. **MQTT 403 Forbidden**: The Supervisor services API rejects credential requests because the add-on manifest lacks `hassio_api: true` and the `mqtt` service declaration. Without credentials, the fallback connects with no auth, and Mosquitto rejects.
2. **Posti scraper silent failure**: When the scraper encounters errors (auth endpoint changes, network issues, rate limiting), it logs a warning but leaves the package at `status: unknown` with no events. No visibility into what went wrong from the UI or logs at INFO level.

## What Changes

- Add `hassio_api: true` to config.yaml (grants access to Supervisor REST API)
- Add `services: [mqtt]` to config.yaml (declares MQTT service dependency to Supervisor)
- Add `homeassistant_api: true` to config.yaml (needed for notify service calls)
- Improve scraper error visibility: log at WARNING with details, track last_error on package
- Add scraper retry with backoff on transient failures (network timeouts, 5xx)

## Non-goals

- Fixing Posti's API if their endpoint is permanently changed (we can only retry/report)
- Adding alternative scrapers for Posti (HTML scraping)
- Changing MQTT topic structure or sensor behavior

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `addon-infrastructure`: Add `hassio_api`, `homeassistant_api`, and `services` declarations to config.yaml manifest
- `carrier-scrapers`: Add retry with backoff for transient errors, track scraper error state on packages
- `mqtt-sensors`: Credential fetching now succeeds (was blocked by missing `hassio_api`)

## Impact

- `addon/config.yaml` — add 3 fields
- `addon/app/services/scraper_service.py` — add retry logic, error tracking
- `addon/app/scrapers/posti.py` — no change needed (already raises ScraperError properly)
- `addon/app/db/models.py` — optionally add `last_error` field to PackageRow
- Database migration — add `last_error` column to packages table
- Requires add-on reinstall or restart for config.yaml changes to take effect
