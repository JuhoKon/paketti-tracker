## 1. Config.yaml Permissions

- [x] 1.1 Add `hassio_api: true` to `addon/config.yaml`
- [x] 1.2 Add `homeassistant_api: true` to `addon/config.yaml`
- [x] 1.3 Add `services: [mqtt]` to `addon/config.yaml` (MQTT service dependency)

## 2. Scraper Retry Logic

- [x] 2.1 Add `_is_retryable(error)` helper to classify transient vs permanent errors
- [x] 2.2 Add retry loop in `_poll_single` (max 2 retries, 5s/15s backoff)
- [x] 2.3 Improve scraper error log message: include tracking_id, vendor, error details at WARNING level
- [x] 2.4 Write pytest tests for retry logic (mock transient + permanent errors)

## 3. Verification

- [x] 3.1 Rebuild Docker image and deploy to HA
- [ ] 3.2 Verify MQTT credential fetch succeeds (no 403 in logs)
- [ ] 3.3 Verify MQTT connects and publishes sensor discovery
- [ ] 3.4 Verify Posti scraper fetches tracking data (package updates from "unknown")
- [x] 3.5 Run existing pytest suite (`python -m pytest tests/addon/ -v`)
