## Context

Paketti Tracker has a working sidebar panel with package list, delivery timeline, add/remove functionality, and an event map. The coordinator polls Posti's GraphQL API every N minutes per config. The integration stores packages in config entry options and exposes one SensorEntity per package.

Current limitations: no way to rename packages after adding, no "last updated" visibility, no proactive notifications, and users must manually enter tracking IDs (no auto-discovery from emails).

## Goals / Non-Goals

**Goals:**
- Allow editing package entries (rename, change carrier) without remove/re-add
- Show per-package "last updated" timestamp in the panel
- Remove the event map to reduce complexity and bundle size
- Let users configure status-change notifications (which transitions, which devices)
- Support IMAP email connection for auto-discovering packages from shipping emails

**Non-Goals:**
- OAuth-based email (Gmail API, Microsoft Graph) — too complex for initial implementation
- Real-time email push (IMAP IDLE) — polling matches existing coordinator pattern
- Editing tracking IDs — immutable identifier by design
- Custom notification templates — use fixed clear messages

## Decisions

### 1. Edit package via WS command `paketti_tracker/edit_package`

Add a new WS command accepting `tracking_id` (identifier, immutable), `name` (optional new name), and `vendor` (optional new carrier). Updates config entry options in-place.

**Alternative considered:** Reuse options flow. Rejected because the panel is the primary management interface now, and a WS command provides instant feedback without navigating away.

### 2. Last updated tracking in coordinator

Add a `last_updated: datetime` field to `TrackingResult`. The coordinator sets this to `utcnow()` after each successful fetch. For skip-delivered packages, retain the last successful fetch time. The panel displays this as relative time ("5 min ago", "2 hours ago").

**Alternative considered:** Use HA entity's `last_updated` attribute. Rejected because that updates on any state write (even if data didn't change), whereas we want "last time fresh data was fetched from carrier."

### 3. Remove event map entirely

Delete `EventMap.tsx`, `EventMapInner.tsx`, `geocoding.ts`. Remove Leaflet dependency from `package.json`. Remove the map rendering from `PackageCard`. This drops ~100KB from the bundle and removes the Nominatim geocoding dependency.

The `event-map` spec will be archived/deprecated. No migration needed since the map has no persistent state.

### 4. Notifications via HA's `notify` service

Use HA's built-in `hass.services.async_call("notify", device_target, ...)` to send notifications. Configuration stored in config entry options:

```python
{
    "notifications": {
        "enabled": True,
        "triggers": ["in_transit", "out_for_delivery", "delivered", "exception"],
        "devices": ["mobile_app_phone_1", "mobile_app_tablet"]
    }
}
```

The coordinator compares previous status → new status after each update. If the transition matches a configured trigger, fire the notification.

**Alternative considered:** Creating a separate automation blueprint. Rejected because it requires users to set up external automations — the whole point is built-in convenience.

**Alternative considered:** Using HA persistent notifications. Rejected because users want push notifications on their phone, not just a HA UI badge.

### 5. Email parsing architecture

New module `email_parser.py` with:
- `EmailClient` class: async IMAP connection using `aioimaplib`
- `EmailParser` class: extracts tracking IDs from email subjects/bodies using regex patterns
- Integration with coordinator: poll emails on a separate (configurable) interval

Email config stored in config entry options (password encrypted via HA's `async_get_clientsession` credential storage pattern):

```python
{
    "email": {
        "enabled": False,
        "imap_server": "imap.gmail.com",
        "imap_port": 993,
        "username": "user@gmail.com",
        "password": "app-password",  # stored encrypted
        "folder": "INBOX",
        "poll_interval_minutes": 30,
        "auto_add": True,  # auto-add discovered packages
        "search_days": 7   # look back N days
    }
}
```

Parsing strategy:
- Search for emails from known senders (Posti, Postnord, Matkahuolto)
- Extract tracking IDs using carrier-specific regex patterns
- Cross-reference with already-tracked packages to avoid duplicates
- If `auto_add` is true, add new packages automatically; otherwise, show them as "discovered" in the panel for user confirmation

### 6. WS commands for new features

| Command | Purpose |
|---------|---------|
| `paketti_tracker/edit_package` | Update name/vendor for existing package |
| `paketti_tracker/get_notifications` | Get notification config |
| `paketti_tracker/update_notifications` | Update notification triggers/devices |
| `paketti_tracker/get_email_config` | Get email settings (password masked) |
| `paketti_tracker/update_email_config` | Update email connection settings |
| `paketti_tracker/test_email_connection` | Test IMAP connection, return success/error |
| `paketti_tracker/discovered_packages` | List packages found in email but not yet tracked |
| `paketti_tracker/confirm_package` | Add a discovered package to tracking |

### 7. Frontend changes

- **Remove:** `EventMap.tsx`, `EventMapInner.tsx`, `geocoding.ts`, Leaflet CSS injection
- **Add:** `EditPackageDialog.tsx` (rename/change carrier modal)
- **Add:** `NotificationSettings.tsx` (in SettingsDrawer — trigger checkboxes, device multi-select)
- **Add:** `EmailSettings.tsx` (in SettingsDrawer — IMAP config, test button, discovered packages list)
- **Modify:** `PackageCard.tsx` — add edit button, show "last updated" relative time, remove map section
- **Modify:** `SettingsDrawer.tsx` — add notification and email sections
- **Remove:** Leaflet from `package.json` dependencies

## Risks / Trade-offs

- [Risk] Email passwords stored in config entry options. Mitigation: Use HA's built-in credential storage helpers; document that app-specific passwords should be used.
- [Risk] IMAP connection may be unreliable (timeouts, auth failures). Mitigation: Graceful error handling; status shown in panel; test-connection command lets user verify before enabling.
- [Risk] Email parsing regex may miss some email formats. Mitigation: Start with known Finnish carrier email templates; log unmatched emails at debug level for future pattern additions.
- [Risk] `aioimaplib` is an external dependency. Mitigation: Add to `manifest.json` requirements; it's a well-maintained async IMAP library.
- [Trade-off] Polling email (not push). Acceptable because the tracking data itself is polled — instant email detection isn't critical when package status updates hourly anyway.
- [Trade-off] Removing the map means losing geographic visualization. Acceptable per user decision — timeline provides the progression view that matters.
