## 1. Backend: WebSocket API

- [x] 1.1 Create `custom_components/paketti_tracker/websocket_api.py` with WS command registration helper
- [x] 1.2 Implement `paketti_tracker/packages` command — returns all packages with full tracking data from coordinator
- [x] 1.3 Implement `paketti_tracker/add_package` command — validates input, updates config entry options, triggers coordinator refresh
- [x] 1.4 Implement `paketti_tracker/remove_package` command — removes from options, removes entity
- [x] 1.5 Implement `paketti_tracker/refresh` command — triggers `async_request_refresh()` on coordinator, returns updated data
- [x] 1.6 Implement `paketti_tracker/get_settings` and `paketti_tracker/update_settings` commands — read/write poll interval
- [x] 1.7 Write pytest tests for all WebSocket commands (success + error cases)

## 2. Backend: Panel Registration

- [x] 2.1 Create `custom_components/paketti_tracker/panel.py` with `async_register_panel()` logic and static file path registration
- [x] 2.2 Update `__init__.py` to call panel registration and WS API setup on `async_setup_entry`
- [x] 2.3 Update `__init__.py` `async_unload_entry` to clean up panel registration
- [x] 2.4 Add `CONF_POLL_INTERVAL` to `const.py` and wire it through coordinator

## 3. Frontend: Project Setup

- [x] 3.1 Create `frontend/` directory with `package.json` (React, TypeScript, Vite, Leaflet dependencies)
- [x] 3.2 Create Vite config for IIFE bundle output to `dist/paketti-tracker-panel.js`
- [x] 3.3 Create `tsconfig.json` with strict mode
- [x] 3.4 Create entry point `src/main.tsx` that receives `hass` object and renders React app
- [x] 3.5 Create HA WebSocket client utility (`src/api.ts`) wrapping `hass.callWS()`

## 4. Frontend: Core Components

- [x] 4.1 Implement `App` component with React Context provider for hass connection and package state
- [x] 4.2 Implement `Header` component — title, refresh button (with loading spinner), settings gear icon
- [x] 4.3 Implement `PackageList` component — maps packages to cards, handles empty state
- [x] 4.4 Implement `PackageCard` component — name, tracking ID, carrier, status badge (color-coded), last event, expand/collapse
- [x] 4.5 Implement `AddPackageDialog` component — modal with tracking ID, carrier select, name fields, validation
- [x] 4.6 Implement `SettingsDrawer` component — poll interval slider/input, save button

## 5. Frontend: Delivery Timeline

- [x] 5.1 Implement `DeliveryTimeline` component — vertical stepper with connected nodes
- [x] 5.2 Add color-coded nodes (green=delivered, blue=transit, gray=pending, red=exception)
- [x] 5.3 Highlight most recent event as active/current state
- [x] 5.4 Handle empty events with "Awaiting first scan" placeholder

## 6. Frontend: Event Map

- [x] 6.1 Implement lazy-loaded `EventMap` component using React.lazy + Suspense for Leaflet
- [x] 6.2 Create geocoding utility (`src/geocoding.ts`) — Nominatim lookup with 1s rate limiting and localStorage cache
- [x] 6.3 Render markers for geocoded event cities connected by polyline route
- [x] 6.4 Handle unresolvable cities gracefully (skip without error)

## 7. Frontend: Styling

- [x] 7.1 Create global styles using HA CSS custom properties (--primary-color, --card-background-color, etc.)
- [x] 7.2 Style PackageCard with status badge colors matching normalized statuses
- [x] 7.3 Style dialogs and drawers consistent with HA Material Design patterns
- [x] 7.4 Add loading states and transitions/animations for smooth UX

## 8. Build and Integration

- [x] 8.1 Build the React app and commit `dist/paketti-tracker-panel.js` to repo (so HACS users don't need Node)
- [x] 8.2 Add build instructions to README
- [x] 8.3 Verify panel loads correctly in HA dev environment
- [x] 8.4 Test full flow: add package from panel, see it appear, expand timeline, view map, remove package
