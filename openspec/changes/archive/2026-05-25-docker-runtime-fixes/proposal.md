## Why

The add-on Docker container fails at runtime on HA OS due to multiple issues discovered during first deployment: s6-overlay PID 1 conflict, missing frontend assets through ingress proxy, MQTT authentication not wired, and configuration value handling. These must be fixed for the add-on to be usable.

## What Changes

- Fix frontend asset serving through HA ingress (relative paths via `base: "./"` in Vite)
- Wire MQTT credentials from Supervisor API (currently connecting without auth)
- Harden `run.sh` against bashio returning literal `"null"` strings
- Ensure `FileResponse` serves correct MIME types for CSS/JS
- Add `init: false` to `config.yaml` (prevent tini stealing PID 1 from s6-overlay)
- Fix FastAPI 0.115.6 incompatibility (204 DELETE endpoints need `response_model=None`)
- Add `cd /app` in run.sh (s6 services run from `/`, not WORKDIR)

## Non-goals

- Changing the overall architecture or service boundaries
- Adding new features (Postnord, Matkahuolto scrapers)
- Modifying the database schema

## Capabilities

### New Capabilities

(none — all fixes are within existing capabilities)

### Modified Capabilities

- `addon-infrastructure`: Fix s6-overlay init, run.sh null handling, working directory, Dockerfile multi-stage build
- `frontend-panel`: Fix asset paths for ingress proxy (relative base), MIME types
- `mqtt-sensors`: Wire MQTT credentials from Supervisor services API

## Impact

- `addon/Dockerfile` — multi-stage build, ARG placement
- `addon/config.yaml` — add `init: false`
- `addon/run.sh` — null filtering, cd /app, defaults
- `addon/frontend/vite.config.ts` — `base: "./"` 
- `addon/app/main.py` — MIME types for static files
- `addon/app/routers/packages.py`, `email.py` — 204 response_model fix
- `addon/app/services/mqtt_service.py` — fetch credentials from Supervisor API
