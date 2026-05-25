## Context

The add-on was developed and tested with unit tests (`pytest-asyncio`) and a local venv, but the first real deployment to HA OS revealed multiple runtime issues. The Docker build now succeeds, but the container fails to start properly or serve the frontend through the HA ingress proxy.

Current state: s6-overlay, module loading, config parsing, and DB migration all work after prior fixes. Remaining issues are frontend asset paths and MQTT authentication.

## Goals / Non-Goals

**Goals:**
- Frontend assets load correctly through HA ingress proxy
- MQTT connects with proper credentials from Supervisor services API
- Container runs reliably with no crash loops

**Non-Goals:**
- Adding new features or scrapers
- Changing the database schema
- WebSocket support or real-time updates

## Decisions

### D1: Relative asset paths via `base: "./"` in Vite

**Choice**: Set `base: "./"` in `vite.config.ts` so all asset references in built HTML use relative paths (`./assets/...`).

**Rationale**: HA ingress serves the add-on at `/api/hassio_ingress/<session_token>/`. Absolute paths like `/assets/...` resolve against the HA root, bypassing the add-on entirely. Relative paths resolve against the current URL, which correctly routes through ingress.

**Alternative considered**: Dynamically rewriting HTML at serve-time to inject the ingress base path into asset URLs. Rejected — fragile and unnecessary when Vite natively supports relative base.

### D2: MQTT credentials from Supervisor services API

**Choice**: At startup, call `GET /services/mqtt` on the Supervisor API (via `SUPERVISOR_TOKEN`) to retrieve MQTT broker host, port, username, and password. Fall back to `core-mosquitto:1883` with no auth if the API call fails.

**Rationale**: HA Supervisor provides MQTT credentials via its services API — this is the standard pattern for add-ons. Hardcoding or config-file credentials would break portability.

**Alternative considered**: Reading from environment variables set by Supervisor. Rejected — Supervisor exposes MQTT via API, not env vars (unlike `SUPERVISOR_TOKEN`).

### D3: Explicit MIME types in FileResponse

**Choice**: Use `mimetypes.guess_type()` and pass `media_type=` to `FileResponse`.

**Rationale**: Some Alpine/musl environments have incomplete MIME type databases. Starlette's default detection may return `application/octet-stream` for `.css` files, causing browsers to reject stylesheets with strict MIME checking.

### D4: s6-overlay run.sh with `cd /app`

**Choice**: `cd /app` before `exec uvicorn` in `run.sh`.

**Rationale**: s6-overlay services run with `/` as working directory. `uvicorn app.main:app` requires the working directory to contain the `app` package for Python import resolution.

## Risks / Trade-offs

- **[Risk]** MQTT Supervisor API may not be available if Mosquitto isn't installed → **Mitigation**: Graceful fallback with 30s retry loop; service continues without MQTT (sensors just won't publish)
- **[Risk]** `mimetypes` database varies across environments → **Mitigation**: Only used for common web types (.css, .js, .html) which are universally registered
- **[Trade-off]** `base: "./"` means the SPA can't use absolute URL references in JavaScript for API calls → **Mitigation**: API client already uses relative URLs (`/api/...`) which resolve correctly from the ingress path
