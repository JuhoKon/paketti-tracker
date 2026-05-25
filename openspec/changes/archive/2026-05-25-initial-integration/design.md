## Context

paketti-tracker is a new Home Assistant custom integration with no prior codebase. It needs to track postal packages from Finnish and Nordic carriers (Posti, Postnord, Matkahuolto) inside HA, exposing package state as sensor entities so users can build notification automations without leaving the HA ecosystem.

The integration is for personal use, installed via HACS.

## Goals / Non-Goals

**Goals:**
- Provide a working HA integration that tracks packages from three carriers
- Require zero API credentials from the user
- Expose normalized, automation-friendly sensor states
- Fit naturally into HA conventions (config entry, options flow, DataUpdateCoordinator, recorder)

**Non-Goals:**
- UPS support (deferred)
- Custom Lovelace card
- Multi-user / shared tracking
- Automatic package discovery from email
- Batched / optimized scraping (one request per package)

## Decisions

### ADR-001: Scraping over official APIs

**Decision:** All carrier data is obtained by calling the same internal JSON endpoints that each carrier's public tracking website uses. No official API keys or developer programme registration required.

**Rationale:** This is a personal tool. The setup friction of registering for three separate developer APIs, rotating credentials, and handling OAuth flows would make the integration impractical. The internal endpoints used by carrier tracking pages are stable enough for personal use and are freely accessible.

**Alternatives considered:**
- *Official APIs* — Posti and Postnord have official APIs, but both require registration and credentials, adding setup steps and credential-management surface area.
- *HTML scraping* — more brittle than calling the underlying JSON endpoints the pages rely on. Internal JSON endpoints are the preferred approach; HTML scraping is a fallback only.

**Trade-off accepted:** Scrapers can break silently when vendors update their sites. Mitigated by surfacing `unavailable` state rather than stale data, and by isolating each scraper so one breakage does not affect others.

---

### ADR-002: Single config entry, options flow for package management

**Decision:** One config entry for the whole integration. Users add and remove packages via the options flow (the "Configure" button in the HA integrations UI). No services or YAML required.

**Rationale:** A single entry keeps setup to one click. The options flow is the standard HA mechanism for post-install configuration. Managing a list of packages via two flow steps (action selector → add form or remove multi-select) is sufficient for personal use.

**Alternatives considered:**
- *One config entry per carrier* — would allow per-carrier credentials in future, but unnecessary complexity now given the no-credentials decision.
- *HA service actions (`add_package`, `remove_package`)* — more powerful and automation-friendly, but adds surface area for an MVP. Can be added later without breaking changes.

---

### ADR-003: Normalized status model

**Decision:** All scrapers map carrier-specific status strings to a fixed vocabulary: `pending`, `in_transit`, `out_for_delivery`, `delivered`, `exception`, `unknown`.

**Rationale:** Carriers use different terminology (Finnish, Swedish, English; different phrasing). A normalized vocabulary lets a single automation cover all carriers: `trigger on state change to delivered`.

**Alternatives considered:**
- *Raw carrier strings as state* — simpler to implement, but makes cross-carrier automations impossible and breaks if a carrier changes their wording.

---

### ADR-004: Stop polling on delivery, persist entity until removed

**Decision:** Once a package transitions to `delivered`, the coordinator stops issuing scrape requests for it. The sensor entity remains in HA with state `delivered` until the user removes it via the options flow.

**Rationale:** Delivered packages do not change state. Continuing to poll wastes requests and may trigger rate limits. Keeping the entity lets users see delivery history in HA's recorder and remove packages on their own schedule.

**Alternatives considered:**
- *Auto-remove after N days* — adds complexity and removes user control.
- *Continue polling at reduced frequency* — unnecessary; delivery is a terminal state.

**Implementation note:** On HA restart the coordinator will issue one fetch per delivered-but-not-removed package to re-establish state, then skip further fetches. This is acceptable.

---

### ADR-005: httpx for async HTTP

**Decision:** Use `httpx` (async client) as the HTTP library for all scraper requests.

**Rationale:** `httpx` is async-native, has a clean API, supports HTTP/2, and handles cookies and redirects well — all useful for mimicking browser requests to carrier sites. It is widely used in the HA ecosystem.

**Alternatives considered:**
- *aiohttp* — HA's built-in session (`async_get_clientsession`) uses aiohttp. Using the HA-provided session is idiomatic, avoids managing connection lifecycle, and is the preferred approach for integrations that do not need special HTTP/2 or client certificate features. Reconsidering: **using `async_get_clientsession(hass)` (aiohttp) is preferred** to avoid an extra dependency and align with HA conventions.

**Revised decision:** Use `hass.async_get_clientsession()` (aiohttp-backed) rather than a standalone `httpx` client. No extra `manifest.json` dependency needed.

---

### ADR-006: One SensorEntity per package, sensor platform only

**Decision:** Each tracked package is represented as a single `SensorEntity`. State = normalized status string. All other data (estimated delivery, events, location) exposed as attributes.

**Rationale:** The primary use case is notification automations triggered by state change. A single sensor is sufficient. `estimated_delivery` as a separate sensor would enable date-based automations but adds complexity; it can be added later. HA's recorder automatically persists state history.

**Alternatives considered:**
- *BinarySensorEntity for delivered/not-delivered* — loses intermediate state (in_transit, out_for_delivery, exception).
- *Separate sensors for each attribute* — adds entity clutter for marginal automation gain at this stage.

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| Carrier updates its internal endpoint → scraper breaks | Entity state becomes `unavailable`; other carriers unaffected; fix scraper in isolation |
| HA session cookie / header mimicry insufficient → 403/429 | Per-scraper request headers tuned to match browser; add retry with backoff |
| Large `events` attribute list → HA recorder truncation | Cap stored events at last 10; full history available on carrier site |
| Options flow list management is awkward UX | Accepted for MVP; service actions can be added later |
| HA restart causes one extra fetch per delivered package | Accepted; at hourly polling this is negligible |

## Migration Plan

This is the initial version of the integration. No migration required.

Installation path:
1. Add repository to HACS
2. Install integration via HACS
3. Add integration via HA Settings → Integrations → Add
4. Use "Configure" button to add tracked packages

Rollback: uninstall via HACS, remove config entry.

## Open Questions

- Minimum HA version: needs confirmation against `DataUpdateCoordinator` and `OptionsFlowHandler` API versions in use. Target: current stable minus one minor version.
- Postnord endpoint language: their API may return descriptions in Swedish by default; confirm if a `?locale=fi` or `Accept-Language` header switches to Finnish/English.
- Matkahuolto endpoint: needs reverse-engineering spike to confirm whether a JSON endpoint exists or HTML parsing is required.
