## Why

Email IMAP settings (host, port, username, password, folder) are currently only configurable through the add-on web UI and stored in SQLite. This means users cannot configure email before the UI is accessible, and there's no integration with HA's standard add-on configuration flow. Moving email settings to the add-on Options (config.yaml schema) provides a consistent configuration experience and allows setup before first launch.

## What Changes

- Add email IMAP fields to `config.yaml` options/schema (host, port, username, password, folder, enabled, auto_add)
- Read email config from add-on options (via bashio/env vars) in addition to the database
- Add-on options become the source of truth for email connection settings
- Frontend settings page still displays email config but reads from the same source
- Remove the REST API email config write endpoint (config is managed via HA Options now)

## Non-goals

- Changing how discovered packages work
- Modifying the email parser logic
- Supporting multiple email accounts

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `addon-infrastructure`: Add email IMAP fields to config.yaml options and schema
- `email-parsing`: Email client reads connection settings from add-on options (env vars) instead of database

## Impact

- `addon/config.yaml` — new options and schema entries for email
- `addon/run.sh` — export email env vars from bashio::config
- `addon/app/config.py` — add email fields to Settings dataclass
- `addon/app/services/email_service.py` — use Settings for connection params
- `addon/app/routers/email.py` — remove PUT config endpoint, GET returns from Settings
- `addon/frontend/src/components/SettingsPage.tsx` — show email config as read-only (configured via HA Options)
