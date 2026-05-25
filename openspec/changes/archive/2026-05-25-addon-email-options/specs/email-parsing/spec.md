## MODIFIED Requirements

### Requirement: Standalone IMAP client

The email parsing module SHALL use a standalone IMAP client (aioimaplib or similar) that does not depend on Home Assistant's event loop or client session. Connection settings SHALL be read from the application Settings (sourced from add-on options via environment variables), not from the database.

#### Scenario: IMAP connection uses add-on options
- **WHEN** the email polling task connects to the IMAP server
- **THEN** it SHALL use host, port, username, and password from the Settings dataclass (populated from env vars)

#### Scenario: Email service inactive when disabled
- **WHEN** email_enabled is false OR email_host is empty
- **THEN** the email service SHALL not attempt any IMAP connections

#### Scenario: Email parsing behavior unchanged
- **WHEN** an email containing a tracking number is processed
- **THEN** the extracted tracking_id and vendor SHALL be identical to the previous implementation's output

---

## ADDED Requirements

### Requirement: Email config read-only API

The REST API SHALL provide a GET endpoint that returns the current email configuration (from Settings) for display in the frontend. No write endpoint SHALL exist for email connection settings.

#### Scenario: GET returns current config from options
- **WHEN** a GET request is made to /api/email
- **THEN** the response SHALL include enabled, host, port, username, password_set (boolean), folder, and auto_add fields sourced from Settings

#### Scenario: No PUT endpoint for email config
- **WHEN** a PUT request is made to /api/email
- **THEN** the response SHALL be 405 Method Not Allowed

### Requirement: Frontend displays config as read-only

The settings page SHALL display email configuration as read-only fields with a message directing users to configure email in HA add-on Options.

#### Scenario: Settings page shows email config
- **WHEN** the user views the settings page
- **THEN** email host, port, username, and folder SHALL be displayed as read-only
- **AND** a message SHALL indicate "Configure in Add-on Options"
