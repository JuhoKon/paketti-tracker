## ADDED Requirements

### Requirement: HA REST API notification dispatch

The system SHALL call the HA REST API at http://supervisor/core/api/services/notify/{device} using the SUPERVISOR_TOKEN as Bearer authentication to send notifications.

#### Scenario: Notification sent successfully
- **WHEN** a package status changes to a configured trigger status
- **THEN** the system SHALL POST to the notify service endpoint with title and message body

#### Scenario: Authentication via SUPERVISOR_TOKEN
- **WHEN** the notification HTTP request is made
- **THEN** the Authorization header SHALL be "Bearer {SUPERVISOR_TOKEN}"

---

### Requirement: Trigger-based notification firing

Notifications SHALL fire on status changes matching the user's configured trigger statuses.

#### Scenario: Matching trigger fires notification
- **WHEN** a package transitions to a status in the configured triggers list
- **THEN** a notification SHALL be sent to all configured devices

#### Scenario: Non-matching transition is silent
- **WHEN** a package transitions to a status NOT in the configured triggers list
- **THEN** no notification SHALL be sent

---

### Requirement: No notification on first poll

The system SHALL NOT send a notification on the first poll for a package (when there is no previous status to compare against).

#### Scenario: First poll suppressed
- **WHEN** a newly added package is polled for the first time
- **THEN** no notification SHALL be sent regardless of the status

---

### Requirement: No notification when status unchanged

The system SHALL NOT send a notification when the status is the same as the previous poll.

#### Scenario: Status unchanged
- **WHEN** a package is polled and the status has not changed
- **THEN** no notification SHALL be sent

---

### Requirement: Graceful error handling

HA API errors SHALL be logged as warnings without crashing the application.

#### Scenario: HA API returns error
- **WHEN** the notify endpoint returns a non-2xx response
- **THEN** the system SHALL log a warning and continue normal operation

#### Scenario: HA API unreachable
- **WHEN** the HTTP request to the notify endpoint times out
- **THEN** the system SHALL log a warning and continue normal operation

---

### Requirement: Multiple target devices

The system SHALL support sending notifications to multiple configured devices.

#### Scenario: Two devices configured
- **WHEN** a trigger event occurs with two devices configured
- **THEN** a notification SHALL be sent to each device independently
