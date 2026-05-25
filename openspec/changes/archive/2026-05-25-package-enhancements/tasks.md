## 1. Remove Event Map

- [x] 1.1 Remove `EventMap.tsx`, `EventMapInner.tsx`, `geocoding.ts` from frontend source
- [x] 1.2 Remove Leaflet and `@types/leaflet` from `package.json` dependencies
- [x] 1.3 Remove map rendering section from `PackageCard.tsx`
- [x] 1.4 Remove Leaflet CSS inline import from `EventMapInner.tsx` references
- [x] 1.5 Rebuild frontend bundle and verify reduced size

## 2. Backend: Edit Package & Last Updated

- [x] 2.1 Add `last_updated: datetime | None` field to `TrackingResult` in `models.py`
- [x] 2.2 Update coordinator `_async_update_data` to set `last_updated = utcnow()` on successful fetch; preserve on error/skip
- [x] 2.3 Add `tracking_url` helper to `const.py` (URL templates per vendor) and expose in `_serialize_tracking_result`
- [x] 2.4 Add `ws_edit_package` WS command in `websocket_api.py` — update name/vendor in config entry options
- [x] 2.5 Update `ws_packages` response to include `last_updated` and `tracking_url` fields
- [x] 2.6 Write pytest tests for edit_package (success, not_found) and last_updated behavior

## 3. Backend: Notifications

- [x] 3.1 Add notification config constants to `const.py` (CONF_NOTIFICATIONS, default triggers, etc.)
- [x] 3.2 Create `notifications.py` module with `async_send_notification(hass, package_name, status, event_desc, devices)`
- [x] 3.3 Integrate notification dispatch into coordinator: compare old vs new status, fire on trigger match
- [x] 3.4 Add `ws_get_notifications` and `ws_update_notifications` WS commands
- [x] 3.5 Write pytest tests for notification logic (trigger matching, no-op when disabled, device targeting)

## 4. Backend: Email Parsing

- [x] 4.1 Add `aioimaplib` to `manifest.json` requirements and install in dev venv
- [x] 4.2 Create `email_client.py` — async IMAP connect, login, search, fetch email bodies
- [x] 4.3 Create `email_parser.py` — regex patterns for Posti/Postnord/Matkahuolto tracking IDs; extract from subject+body
- [x] 4.4 Add email polling logic to coordinator (separate interval, search window, deduplication)
- [x] 4.5 Add `ws_get_email_config`, `ws_update_email_config`, `ws_test_email_connection` WS commands
- [x] 4.6 Add `ws_discovered_packages`, `ws_confirm_package`, `ws_dismiss_package` WS commands
- [x] 4.7 Write pytest tests for email_client (mock IMAP), email_parser (regex extraction), and WS commands

## 5. Frontend: Edit & Last Updated

- [x] 5.1 Create `EditPackageDialog.tsx` — modal with name input, carrier select, save/cancel
- [x] 5.2 Add edit button (pencil icon) to `PackageCard.tsx` header
- [x] 5.3 Display relative "last updated" time on each PackageCard (e.g. "5 min ago")
- [x] 5.4 Add carrier tracking URL link (external link icon) to PackageCard
- [x] 5.5 Add `editPackage` function to `api.ts`

## 6. Frontend: Notification & Email Settings

- [x] 6.1 Create `NotificationSettings.tsx` — enable toggle, trigger checkboxes, device multi-select
- [x] 6.2 Create `EmailSettings.tsx` — IMAP form fields, test connection button, auto-add toggle, discovered packages list
- [x] 6.3 Integrate `NotificationSettings` and `EmailSettings` into `SettingsDrawer.tsx` as sections
- [x] 6.4 Add WS API functions to `api.ts` (notifications, email config, test connection, discovered/confirm/dismiss)
- [x] 6.5 Update `types.ts` with new interfaces (NotificationConfig, EmailConfig, DiscoveredPackage)

## 7. Frontend: Discovered Packages UI

- [x] 7.1 Create `DiscoveredPackages.tsx` — list of email-discovered packages with confirm/dismiss buttons
- [x] 7.2 Integrate discovered packages section into main panel (below tracked packages or in a tab)
- [x] 7.3 Add notification badge on header when there are pending discovered packages

## 8. Build & Finalize

- [x] 8.1 Rebuild frontend bundle with all changes
- [x] 8.2 Run full test suite (ruff, mypy, pytest) and fix any issues
- [ ] 8.3 Update README with new features (notifications, email parsing, edit)
- [ ] 8.4 Verify panel loads and all new features work end-to-end
