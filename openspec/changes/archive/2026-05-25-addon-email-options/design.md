## Context

Email IMAP configuration is currently stored in the SQLite settings table (key-value JSON) and configured exclusively through the add-on's REST API / React settings page. The HA add-on Options page (`config.yaml` schema) only exposes poll intervals and log level.

HA add-ons have a standard pattern: sensitive configuration (credentials, hosts) goes in the Options schema, which HA presents in its native configuration UI. This provides password masking, validation, and allows configuration before the add-on web UI is loaded.

## Goals / Non-Goals

**Goals:**
- Email IMAP settings configurable from HA add-on Options page
- Settings available as environment variables at startup
- Email service uses these settings directly (no DB round-trip needed)
- Frontend displays current config read-only (since it's managed externally)

**Non-Goals:**
- Supporting multiple email accounts
- Encrypting credentials at rest (HA manages this in its own store)
- Changing email parsing logic or discovered packages flow

## Decisions

### D1: Add-on Options as source of truth for email connection settings

**Choice**: Email IMAP connection settings (host, port, username, password, folder, enabled, auto_add) are defined in `config.yaml` options/schema. They flow through `bashio::config` → env vars → `Settings` dataclass.

**Rationale**: This is the HA standard. Users expect to configure add-on credentials in the Options tab. It also means the add-on can connect to IMAP immediately on first boot without waiting for web UI interaction.

**Alternative considered**: Keep dual-source (DB + options) with options as fallback. Rejected — confusing UX with two places to configure the same thing.

### D2: Password field uses `password` schema type

**Choice**: Use HA's `password` schema type for the IMAP password field, which masks it in the UI.

**Rationale**: HA Supervisor natively supports password masking in add-on options. No custom handling needed.

### D3: Optional fields with empty defaults

**Choice**: Email fields default to empty strings (disabled state). The email service only activates when `email_enabled` is true AND host/username/password are non-empty.

**Rationale**: Not all users want email parsing. Empty defaults = opt-in behavior. The `email_enabled` boolean provides an explicit toggle.

### D4: Remove email config write endpoint from REST API

**Choice**: Remove `PUT /api/email` endpoint. The `GET /api/email` endpoint remains but returns config from Settings (env vars) instead of database.

**Rationale**: If options are the source of truth, allowing writes via REST creates conflict. Frontend shows the config read-only with a note to configure via HA Options.

## Risks / Trade-offs

- **[Trade-off]** Users must restart the add-on after changing email options (HA pattern) → **Mitigation**: HA shows a "restart required" prompt automatically when options change
- **[Risk]** Existing users with email config in DB will lose it on upgrade → **Mitigation**: Document in changelog; email config is simple to re-enter in Options
- **[Trade-off]** Frontend can no longer edit email settings inline → **Mitigation**: Show "Configure in Add-on Options" link/message in the settings page
