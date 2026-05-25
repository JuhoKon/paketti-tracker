## 1. Project Scaffold

- [x] 1.1 Create `custom_components/paketti_tracker/` directory structure with empty `__init__.py`, `manifest.json`, `const.py`, `models.py`
- [x] 1.2 Write `manifest.json` with domain, name, version, HA min version, and `config_flow: true`
- [x] 1.3 Define constants in `const.py`: `DOMAIN`, vendor identifier strings (`VENDOR_POSTI`, `VENDOR_POSTNORD`, `VENDOR_MATKAHUOLTO`), normalized status constants
- [x] 1.4 Define `TrackingEvent` and `TrackingResult` dataclasses in `models.py`
- [x] 1.5 Create `scrapers/` subdirectory with empty `__init__.py`, `base.py`

## 2. Scraper Base and Factory

- [x] 2.1 Define abstract `BaseScraper` in `scrapers/base.py` with `async def fetch(tracking_id, session) -> TrackingResult` and `ScraperError` exception class
- [x] 2.2 Implement scraper factory `get_scraper(vendor: str) -> BaseScraper` in `scrapers/__init__.py`; raise `ValueError` for unknown vendor
- [x] 2.3 Write pytest tests for the factory (known vendors return correct type, unknown raises `ValueError`)

## 3. Posti Scraper

- [x] 3.1 Reverse-engineer Posti's internal tracking endpoint — discovered GraphQL at `graphql.posti.fi` with anonymous auth from `auth-service.posti.fi`
- [x] 3.2 Implement `PostiScraper` in `scrapers/posti.py` using `aiohttp` session; anonymous token auth + SearchShipments GraphQL query; parse response into `TrackingResult`
- [x] 3.3 Build Posti status-to-normalized mapping (WAITING/ORDER_RECEIVED→pending, RECEIVED/IN_TRANSPORT→in_transit, IN_DELIVERY→out_for_delivery, READY_FOR_PICKUP/DELIVERED→delivered, RETURN_*→exception)
- [x] 3.4 Write pytest tests for `PostiScraper` (11 tests: success, delivered, exception, not-found, auth error, HTTP error, token reuse, token invalidation, reason text, status map)

## 4. Postnord Scraper (deferred)

- [ ] 4.1 Deferred — not in current scope

## 5. Matkahuolto Scraper (deferred)

- [ ] 5.1 Deferred — not in current scope

## 6. Coordinator

- [x] 6.1 Implement `PakettiCoordinator(DataUpdateCoordinator)` in `coordinator.py` with 60-minute update interval
- [x] 6.2 In `_async_update_data`: iterate packages from config entry options, skip delivered, call correct scraper, return `dict[tracking_id, TrackingResult]`
- [x] 6.3 Handle `ScraperError` per package: log warning, preserve previous result on transient failure; exclude from data if no previous (→ entity unavailable)
- [x] 6.4 Write pytest tests for coordinator: all-success, partial scrape failure, skip-delivered logic, empty packages

## 7. Config Flow and Options Flow

- [x] 7.1 Implement `PakettiConfigFlow` in `config_flow.py` with a single setup step (creates the config entry)
- [x] 7.2 Implement `PakettiOptionsFlow` step 1: action selector (Add / Remove)
- [x] 7.3 Implement options flow step 2a (Add): form with `tracking_id` (text), `vendor` (select), `name` (text, optional); validate no duplicate tracking ID; normalize to uppercase
- [x] 7.4 Implement options flow step 2b (Remove): multi-select of current packages; remove selected entries from options
- [x] 7.5 Write pytest tests for config flow setup and both options flow paths (8 tests)

## 8. Sensor Platform

- [x] 8.1 Implement `async_setup_entry` in `sensor.py`; create one `PakettiSensor` per package from coordinator data
- [x] 8.2 Implement `PakettiSensor(CoordinatorEntity, SensorEntity)`: `native_value` = normalized status, `extra_state_attributes` = all `TrackingResult` fields (events capped at 10)
- [x] 8.3 Handle missing coordinator data for a package (entity reports `unavailable`)
- [x] 8.4 Wire entity addition and removal to options updates (reload on options change)
- [x] 8.5 Write pytest tests for sensor: state mapping, attribute population, unavailable on missing data, events cap (12 tests)

## 9. Integration Entry Point and Translations

- [x] 9.1 Implement `async_setup_entry` and `async_unload_entry` in `__init__.py`; instantiate and start coordinator
- [x] 9.2 Create `translations/en.json` with config flow and options flow strings
- [x] 9.3 Verify integration loads cleanly in a local HA dev environment (no errors in logs)

## 10. Tooling and Quality

- [x] 10.1 Add `pyproject.toml` with ruff, mypy, pytest, and black configuration
- [x] 10.2 Add pytest config in `pyproject.toml` (asyncio_mode = "auto")
- [x] 10.3 Run ruff + mypy across all modules; fix all issues (0 errors)
- [x] 10.4 Add `README.md` with installation instructions (HACS + manual) and basic usage guide
- [x] 10.5 Add `.gitignore`
