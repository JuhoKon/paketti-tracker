## MODIFIED Requirements

### Requirement: Standalone IMAP client

The email parsing module SHALL use a standalone IMAP client (aioimaplib or similar) that does not depend on Home Assistant's event loop or client session. The parsing logic and carrier detection rules remain unchanged.

#### Scenario: IMAP connection independent of HA
- **WHEN** the email polling task connects to the IMAP server
- **THEN** it SHALL use its own asyncio-compatible IMAP client without any HA dependencies

#### Scenario: Email parsing behavior unchanged
- **WHEN** an email containing a tracking number is processed
- **THEN** the extracted tracking_id and vendor SHALL be identical to the previous implementation's output
