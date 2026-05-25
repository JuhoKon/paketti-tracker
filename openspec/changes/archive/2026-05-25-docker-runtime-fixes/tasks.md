## 1. Frontend Asset Path Fix

- [x] 1.1 Set `base: "./"` in `addon/frontend/vite.config.ts`
- [x] 1.2 Add explicit MIME type detection in `spa_fallback` FileResponse (`addon/app/main.py`)
- [x] 1.3 Rebuild frontend and verify index.html contains relative `./assets/` paths
- [x] 1.4 Test asset serving locally via Docker (curl CSS/JS endpoints, check Content-Type headers)

## 2. MQTT Credential Fetching

- [x] 2.1 Add `_fetch_mqtt_credentials()` method to `addon/app/services/mqtt_service.py` that calls Supervisor API
- [x] 2.2 Use fetched credentials in MQTT connect (host, port, username, password)
- [x] 2.3 Re-fetch credentials on reconnect attempts
- [x] 2.4 Fallback to core-mosquitto:1883 with no auth if API unavailable
- [x] 2.5 Write pytest test for credential fetching (mock Supervisor API response)

## 3. Run.sh Hardening

- [x] 3.1 Filter literal "null" strings from bashio::config output in `addon/run.sh`
- [x] 3.2 Add `cd /app` before uvicorn exec
- [x] 3.3 Validate log level with case statement, default to "info"

## 4. Config & Dockerfile Fixes

- [x] 4.1 Add `init: false` to `addon/config.yaml`
- [x] 4.2 Move `ARG BUILD_FROM` before first FROM in Dockerfile
- [x] 4.3 Remove deprecated `build.yaml` (Supervisor passes BUILD_FROM directly)
- [x] 4.4 Fix 204 DELETE endpoints: add `response_model=None` to packages.py and email.py

## 5. Integration Testing

- [x] 5.1 Docker build succeeds locally (`docker build --build-arg BUILD_FROM=... -t paketti-test ./addon`)
- [x] 5.2 Container starts without errors (s6-overlay → uvicorn → app ready)
- [x] 5.3 `GET /` returns HTML with relative asset paths
- [x] 5.4 `GET /assets/index-*.css` returns 200 with Content-Type: text/css
- [x] 5.5 `GET /api/health` returns 200 with {"status": "healthy"}
- [x] 5.6 MQTT logs show credential fetch attempt (warning expected without real Supervisor)
- [x] 5.7 Existing pytest suite still passes (`python -m pytest tests/addon/ -v`)
