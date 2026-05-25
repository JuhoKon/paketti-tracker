## ADDED Requirements

### Requirement: Edit package command

The integration SHALL expose a WebSocket command `paketti_tracker/edit_package` accepting `tracking_id` (string, identifier), `name` (optional string), and `vendor` (optional string).

#### Scenario: Successful rename
- **WHEN** the panel sends `paketti_tracker/edit_package` with a new name
- **THEN** the package's name SHALL be updated in config entry options

#### Scenario: Change carrier
- **WHEN** the panel sends `paketti_tracker/edit_package` with a new vendor
- **THEN** the package's vendor SHALL be updated and coordinator SHALL refresh

#### Scenario: Package not found
- **WHEN** `paketti_tracker/edit_package` is called with an unknown tracking ID
- **THEN** the response SHALL return an error with code "not_found"

### Requirement: Notification configuration commands

The integration SHALL expose `paketti_tracker/get_notifications` and `paketti_tracker/update_notifications` WebSocket commands.

#### Scenario: Get notification config
- **WHEN** the panel sends `paketti_tracker/get_notifications`
- **THEN** the response SHALL include `enabled` (boolean), `triggers` (string array), and `devices` (string array)

#### Scenario: Update notification config
- **WHEN** the panel sends `paketti_tracker/update_notifications` with new triggers and devices
- **THEN** the config entry options SHALL be updated with the new notification settings

### Requirement: Email configuration commands

The integration SHALL expose `paketti_tracker/get_email_config`, `paketti_tracker/update_email_config`, and `paketti_tracker/test_email_connection` WebSocket commands.

#### Scenario: Get email config (password masked)
- **WHEN** the panel sends `paketti_tracker/get_email_config`
- **THEN** the response SHALL include all email settings with the password masked (e.g. "••••••••")

#### Scenario: Update email config
- **WHEN** the panel sends `paketti_tracker/update_email_config` with new settings
- **THEN** the config entry options SHALL be updated and email polling SHALL restart with new settings

#### Scenario: Test email connection success
- **WHEN** the panel sends `paketti_tracker/test_email_connection`
- **THEN** the system SHALL attempt IMAP login and return `{"success": true}` on success

#### Scenario: Test email connection failure
- **WHEN** the panel sends `paketti_tracker/test_email_connection` with invalid credentials
- **THEN** the system SHALL return `{"success": false, "error": "<message>"}` with a descriptive error

### Requirement: Discovered packages commands

The integration SHALL expose `paketti_tracker/discovered_packages` and `paketti_tracker/confirm_package` WebSocket commands.

#### Scenario: List discovered packages
- **WHEN** the panel sends `paketti_tracker/discovered_packages`
- **THEN** the response SHALL include an array of packages found in email but not yet tracked, each with tracking_id, vendor, source_email_subject, and discovered_at

#### Scenario: Confirm discovered package
- **WHEN** the panel sends `paketti_tracker/confirm_package` with a tracking_id
- **THEN** the package SHALL be added to tracking and removed from the discovered list

#### Scenario: Dismiss discovered package
- **WHEN** the panel sends `paketti_tracker/dismiss_package` with a tracking_id
- **THEN** the package SHALL be removed from discovered list and added to a dismissed list to prevent re-discovery
