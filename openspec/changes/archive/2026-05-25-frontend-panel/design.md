## Context

Paketti Tracker is a working HA custom integration with sensor entities for each tracked package. Users currently manage packages via the HA options flow (Settings → Integrations → Configure). There's no visual dashboard — just raw entity states. HACS-style sidebar panels are the standard pattern for integrations that need richer UX.

HA custom panels work by:
1. Registering a panel via `async_register_panel()` with a URL path and JS entry point
2. HA serves the JS file from the integration's static directory
3. The panel JS receives the `hass` object and renders its own UI
4. Communication with backend uses HA's WebSocket API

## Goals / Non-Goals

**Goals:**
- Provide a unified, visually appealing view for all tracked packages
- Allow package management (add/remove) without leaving the panel
- Show delivery timeline with event progression
- Show event locations on a map
- Let users configure poll interval from the panel
- Follow HA's Material Design conventions (colors, spacing, typography)

**Non-Goals:**
- Replacing sensor entities (they stay for automations)
- Server-side rendering
- Offline/PWA support beyond what HA provides
- Real-time updates faster than coordinator interval (WebSocket subscription gives instant UI refresh when coordinator updates, but doesn't change poll frequency)

## Decisions

### 1. React + TypeScript with Vite bundling

The panel uses React 18+ with TypeScript, bundled by Vite into a single IIFE JS file. This gives:
- Fast development with HMR during dev
- Tree-shaking for small production bundle
- TypeScript for type safety with HA's WebSocket types

**Alternative considered:** Lit/Web Components (what HACS uses). Rejected because the user prefers React and the panel is self-contained — no need for Shadow DOM isolation since HA loads the panel in its own frame context.

**Build output:** `custom_components/paketti_tracker/frontend/dist/paketti-tracker-panel.js` — this single file is what HA serves.

### 2. WebSocket API for panel communication

Custom WS commands registered in HA for the panel:
- `paketti_tracker/packages` — list all packages with full tracking data
- `paketti_tracker/add_package` — add a new package
- `paketti_tracker/remove_package` — remove a package
- `paketti_tracker/refresh` — trigger immediate coordinator refresh
- `paketti_tracker/get_settings` — get current settings (poll interval)
- `paketti_tracker/update_settings` — update settings

**Alternative considered:** Using HA service calls + entity state subscriptions. Rejected because WS commands provide a cleaner request/response pattern and can return structured data directly to the panel without entity state indirection.

### 3. Panel registration via `async_register_panel()`

In `__init__.py` during `async_setup_entry`, register the panel:
```python
async_register_panel(
    hass,
    "paketti-tracker",
    frontend_url_path="paketti-tracker",
    sidebar_title="Paketti Tracker",
    sidebar_icon="mdi:package-variant",
    require_admin=False,
    config={"entry_id": entry.entry_id},
)
```

The JS file is served from the integration's `frontend/dist/` directory using `hass.http.register_static_path()`.

### 4. Map implementation with Leaflet + OpenStreetMap

Use Leaflet.js with OSM tiles for the event map. Geocoding of city names uses Nominatim (free, no API key). Cities are geocoded once and cached in the coordinator data to avoid repeated lookups.

**Alternative considered:** Google Maps. Rejected because it requires an API key (violates "no credentials required" principle).

### 5. Panel component architecture

```
App
├── Header (title, refresh button, settings gear)
├── PackageList
│   ├── PackageCard (status badge, name, tracking ID, last event)
│   │   ├── DeliveryTimeline (expandable vertical stepper)
│   │   └── EventMap (Leaflet map, shown on expand)
│   └── EmptyState (when no packages)
├── AddPackageDialog (modal)
└── SettingsDrawer (poll interval, future options)
```

### 6. State management

React Context + useReducer for panel state. No external state library needed — the panel's state is:
- Package list (from WS subscription)
- UI state (selected package, dialogs open/closed, loading states)
- Settings

The panel subscribes to HA state changes for `sensor.paketti_tracker_*` entities to get real-time updates when the coordinator refreshes.

## Risks / Trade-offs

- [Risk] Geocoding city names may be unreliable (e.g. "SEINÄJOKI" works, but abbreviated cities might not). Mitigation: graceful fallback — map shows available points, skips unresolvable cities.
- [Risk] Bundle size with React + Leaflet could be 200-400KB. Mitigation: lazy-load Leaflet only when map is expanded; React is ~40KB gzipped which is acceptable.
- [Risk] Nominatim rate limits (1 req/sec). Mitigation: cache results, batch geocode on coordinator update, not on panel render.
- [Trade-off] Custom WS commands mean panel only works with this integration installed (obvious, but worth noting vs. a generic card approach).
- [Trade-off] React requires Node.js build step. Mitigation: pre-built JS committed to repo so users installing via HACS don't need Node.
