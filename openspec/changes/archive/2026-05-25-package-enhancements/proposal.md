## Why

The panel currently allows adding and removing packages but lacks basic management capabilities users expect: renaming packages, seeing when data was last refreshed, getting notified of status changes, and automatically discovering packages from email. The event map adds bundle size and geocoding complexity for minimal value — users primarily care about status progression, not geographic routing.

## What Changes

- **Remove event map**: Drop the Leaflet/OSM map component and geocoding utility from the panel. Reduces bundle size by ~100KB and removes Nominatim dependency.
- **Edit package entries**: Allow renaming packages and changing carrier from the panel (via new WS command).
- **Last updated timestamp**: Display per-package "last updated" time in the UI showing when tracking data was last successfully fetched.
- **Carrier tracking link**: Each package card links to the carrier's public tracking page (e.g., Posti seuranta) in a new tab.
- **Notification system**: Add configurable notifications — user selects which status transitions trigger notifications and picks target devices (HA mobile app notifications).
- **Email parsing**: Allow users to configure an email account (IMAP) to automatically discover and add new packages from shipping confirmation emails.

## Non-goals

- Editing tracking IDs (immutable identifier — user should remove and re-add instead)
- Supporting email providers via OAuth (initial implementation uses IMAP with app password)
- Push-based email monitoring (poll-based, matching the coordinator pattern)
- SMS/WhatsApp notifications (HA mobile app only for now)

## Capabilities

### New Capabilities
- `notifications`: Configurable status-change notifications sent to selected HA mobile app devices
- `email-parsing`: IMAP email connection, parsing shipping confirmations, auto-adding discovered packages

### Modified Capabilities
- `package-management`: Add edit (rename/change carrier) via WS command; add "last updated" field to tracking data
- `frontend-panel`: Remove EventMap component; add edit dialog, last-updated display, notification settings, email settings to panel
- `panel-websocket-api`: Add `edit_package`, `get_notifications`, `update_notifications`, `get_email_config`, `update_email_config`, `test_email_connection` commands

## Impact

- **Backend**: New `notifications.py` module, new `email_parser.py` module, updated `websocket_api.py`, updated `coordinator.py` (last_updated tracking), updated `models.py`
- **Frontend**: Remove `EventMap.tsx`, `EventMapInner.tsx`, `geocoding.ts`; add `EditPackageDialog.tsx`, `NotificationSettings.tsx`, `EmailSettings.tsx`; update `PackageCard.tsx`, `SettingsDrawer.tsx`
- **Dependencies**: `aioimaplib` for async IMAP; no new HA dependencies for notifications (uses built-in `notify` platform)
- **Config entry options**: Extended with notification preferences, email credentials (encrypted via HA secrets)
- **Entity platforms**: No new platforms (notifications use HA's existing `notify` service)
