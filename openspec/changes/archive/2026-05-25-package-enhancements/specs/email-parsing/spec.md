## ADDED Requirements

### Requirement: IMAP email connection

The system SHALL support connecting to an IMAP email server to read emails for package discovery.

#### Scenario: Successful IMAP connection
- **WHEN** the user provides valid IMAP server, port, username, and password
- **THEN** the system SHALL establish an async IMAP connection and confirm access

#### Scenario: Failed IMAP connection
- **WHEN** the IMAP credentials are invalid or server is unreachable
- **THEN** the system SHALL return a clear error message without crashing

#### Scenario: Test connection command
- **WHEN** the user triggers `paketti_tracker/test_email_connection` via WebSocket
- **THEN** the system SHALL attempt connection and return success or error details

### Requirement: Email polling

The system SHALL periodically poll the configured email folder for new shipping confirmation emails.

#### Scenario: Poll interval respected
- **WHEN** email polling is enabled with a 30-minute interval
- **THEN** the system SHALL check for new emails every 30 minutes

#### Scenario: Search window
- **WHEN** polling for emails
- **THEN** the system SHALL only examine emails from the last N days (configurable, default 7)

### Requirement: Tracking ID extraction from emails

The system SHALL parse email subjects and bodies to extract tracking IDs from known Finnish carriers.

#### Scenario: Posti tracking ID found in email body
- **WHEN** an email contains a string matching Posti tracking ID format (e.g. JJFI followed by digits)
- **THEN** the system SHALL extract it and identify the carrier as Posti

#### Scenario: Multiple tracking IDs in one email
- **WHEN** an email contains multiple tracking IDs
- **THEN** the system SHALL extract all of them as separate discovered packages

#### Scenario: Already-tracked ID found
- **WHEN** a discovered tracking ID is already in the tracked packages list
- **THEN** it SHALL NOT be added to the discovered list (deduplicated)

### Requirement: Auto-add discovered packages

When auto-add is enabled, the system SHALL automatically add newly discovered packages to tracking without user confirmation.

#### Scenario: Auto-add enabled
- **WHEN** auto-add is enabled and a new tracking ID is discovered
- **THEN** the package SHALL be automatically added to config entry options and coordinator SHALL refresh

#### Scenario: Auto-add disabled
- **WHEN** auto-add is disabled and a new tracking ID is discovered
- **THEN** the package SHALL appear in the "discovered packages" list for user to manually confirm

### Requirement: Discovered packages list

The system SHALL maintain a list of packages discovered from email that haven't been added to tracking yet (when auto-add is disabled).

#### Scenario: User confirms discovered package
- **WHEN** the user confirms a discovered package via `paketti_tracker/confirm_package`
- **THEN** the package SHALL be added to tracking and removed from the discovered list

#### Scenario: User dismisses discovered package
- **WHEN** the user dismisses a discovered package
- **THEN** the package SHALL be removed from the discovered list and not re-discovered from the same email

### Requirement: Email configuration persistence

Email settings (server, port, username, password, folder, intervals) SHALL be persisted in config entry options across HA restarts.

#### Scenario: Settings survive restart
- **WHEN** HA is restarted
- **THEN** email settings SHALL be restored and polling SHALL resume if enabled
