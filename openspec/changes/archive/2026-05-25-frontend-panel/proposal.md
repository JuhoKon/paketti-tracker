## Why

The integration currently only exposes sensor entities — users must navigate to Developer Tools or entity cards to see tracking status. There's no unified view showing all packages, their timelines, or management controls. A dedicated sidebar panel (like HACS has) provides a proper home for package tracking with richer UX than entity cards can offer.

## What Changes

- Add a custom HA sidebar panel ("Paketti Tracker" tab) accessible from the left navigation
- Panel displays all tracked packages with status, delivery timeline, and event map
- Add/remove packages directly from the panel (no need to go through integration options)
- Manual refresh button triggers immediate data update
- Settings section for configuring poll interval
- React + TypeScript frontend compiled to a single JS bundle served by HA
- Backend: register panel via `async_register_panel()`, add WebSocket API commands for package management and data retrieval

## Non-goals

- Mobile app / companion app integration
- Push notifications (HA automations handle this already)
- Multi-language panel UI (English only for MVP; translations can come later)
- Replacing the existing sensor entities (they remain for automations/dashboards)

## Capabilities

### New Capabilities

- `frontend-panel`: Custom HA sidebar panel with React UI — package list, add/remove, refresh, settings
- `panel-websocket-api`: WebSocket commands for the panel to manage packages and fetch data without going through options flow
- `delivery-timeline`: Vertical event timeline view per package showing progression through transit
- `event-map`: Leaflet/OpenStreetMap visualization of tracking event locations

### Modified Capabilities

- `package-management`: Add WebSocket-based add/remove commands as alternative to options flow (panel uses WS, options flow remains for non-panel users)

## Impact

- New directory: `custom_components/paketti_tracker/frontend/` (React source + build output)
- New file: `custom_components/paketti_tracker/panel.py` (panel registration)
- New file: `custom_components/paketti_tracker/websocket_api.py` (WS command handlers)
- Modified: `custom_components/paketti_tracker/__init__.py` (register panel + WS commands on setup)
- Build tooling: `package.json`, Vite config, TypeScript config in frontend directory
- New dev dependency: Node.js required for building the panel
