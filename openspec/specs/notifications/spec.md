## ADDED Requirements

### Requirement: Status change notifications

The system SHALL send push notifications to configured HA mobile app devices when a tracked package's status changes to a user-selected trigger status.

#### Scenario: Notification sent on status change
- **WHEN** the coordinator detects a package status transition matching a configured trigger (e.g. `pending` -> `in_transit`)
- **THEN** a notification SHALL be sent to all configured devices via HA's `notify` service with the package name, new status, and last event description

#### Scenario: No notification for non-trigger transitions
- **WHEN** a package status changes to a state not in the configured triggers list
- **THEN** no notification SHALL be sent

#### Scenario: No notification when notifications disabled
- **WHEN** notifications are globally disabled in settings
- **THEN** no notifications SHALL be sent regardless of status changes

### Requirement: Configurable notification triggers

The user SHALL be able to select which status transitions trigger notifications from the set: `in_transit`, `out_for_delivery`, `delivered`, `exception`.

#### Scenario: User selects specific triggers
- **WHEN** the user configures triggers as `["delivered", "exception"]`
- **THEN** only transitions to `delivered` or `exception` SHALL trigger notifications

#### Scenario: Default triggers
- **WHEN** notifications are first enabled
- **THEN** the default triggers SHALL be `["out_for_delivery", "delivered", "exception"]`

### Requirement: Configurable notification devices

The user SHALL be able to select one or more HA mobile app notification targets (devices) to receive notifications.

#### Scenario: Multiple devices configured
- **WHEN** the user selects two devices for notifications
- **THEN** notifications SHALL be sent to both devices on trigger events

#### Scenario: No devices configured
- **WHEN** notifications are enabled but no devices are selected
- **THEN** no notifications SHALL be sent (graceful no-op)

### Requirement: Notification message format

Each notification SHALL include the package name, the new status in human-readable form, and the most recent event description.

#### Scenario: Delivered notification content
- **WHEN** package "Amazon Order" transitions to `delivered` with last event "Ready for pickup at TAMPERE"
- **THEN** the notification title SHALL be "Paketti Tracker" and the message SHALL include "Amazon Order" and "Ready for pickup at TAMPERE"
