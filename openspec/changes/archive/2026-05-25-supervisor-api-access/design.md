## Context

The add-on is deployed on HA OS with Supervisor. Two runtime failures:

1. The MQTT credential fetch (`GET http://supervisor/services/mqtt`) returns 403 because the add-on manifest doesn't declare `hassio_api: true`. The Supervisor only grants API access to add-ons that explicitly request it.

2. The Posti scraper silently fails (ScraperError is caught, logged at WARNING, and the package stays at "unknown" status). The user sees no explanation in the UI — just empty tracking data.

Current state: MQTT falls back to no-auth and gets rejected by Mosquitto. Scraper errors are invisible at INFO log level and from the frontend.

## Goals / Non-Goals

**Goals:**
- MQTT credential fetching succeeds (add-on has Supervisor API access)
- HA REST API calls for notifications succeed (add-on has homeassistant_api access)
- Scraper failures are visible: logged clearly, and optionally surfaced to the user
- Transient scraper failures retry before giving up

**Non-Goals:**
- Changing MQTT behavior beyond credential acquisition
- Fixing Posti API if their endpoint permanently changes
- Adding UI for error display (deferred — log visibility is sufficient for now)

## Decisions

### D1: Add `hassio_api: true` and `homeassistant_api: true` to config.yaml

**Choice**: Declare both API access flags in the add-on manifest.

**Rationale**: `hassio_api: true` grants access to `http://supervisor/*` endpoints (needed for MQTT credential fetch). `homeassistant_api: true` grants access to `http://supervisor/core/api/*` (needed for notify service REST calls). Without these, the add-on gets 403 from Supervisor.

**Alternative considered**: Using the `services` key alone. Rejected — `services: [mqtt]` tells Supervisor this add-on uses MQTT (for dependency ordering) but doesn't grant API access to fetch credentials.

### D2: Add `services: [mqtt]` to config.yaml

**Choice**: Declare MQTT as a required service.

**Rationale**: This tells Supervisor the add-on depends on the MQTT broker. Supervisor will start Mosquitto before this add-on and make MQTT service info available.

### D3: Scraper retry with exponential backoff for transient errors

**Choice**: Retry up to 2 times with 5s/15s delays on network errors (timeouts, connection refused, 5xx responses). Non-retryable errors (4xx, parse errors) fail immediately.

**Rationale**: Posti's auth endpoint occasionally returns transient errors. A single retry is often sufficient. More than 2 retries risks delaying the poll loop for all packages.

**Alternative considered**: Retry at the poll-loop level (re-poll the same package later). Rejected — too complex; the per-fetch retry is simpler and handles the common case.

### D4: Track `last_scraper_error` on PackageRow (deferred)

**Choice**: Defer adding a database column for now. Instead, improve logging to include package tracking_id and error details at WARNING level.

**Rationale**: Adding a DB column + migration + API response field + frontend display is a larger change. The immediate fix is visibility — users running `ha addon logs paketti_tracker` should see clearly which packages failed and why.

## Risks / Trade-offs

- **[Risk]** After adding `hassio_api: true`, the add-on needs a rebuild/reinstall for config.yaml changes to take effect → **Mitigation**: Document in changelog; existing users need to reinstall the add-on
- **[Risk]** Retry delays (up to 20s per package) could slow the poll loop with many packages → **Mitigation**: Only retry on transient errors; cap at 2 retries; parallel polling could be added later
- **[Trade-off]** Not surfacing errors in the UI means users must check logs → **Mitigation**: Acceptable for now; errors are rare and INFO-level logs will show "Updated X: unknown -> in_transit" on success
