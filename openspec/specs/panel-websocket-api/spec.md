## ADDED Requirements

### Requirement: List packages command

The integration SHALL expose a WebSocket command `paketti_tracker/packages` that returns all tracked packages with their full tracking data.

#### Scenario: Successful list
- **WHEN** the panel sends `paketti_tracker/packages`
- **THEN** the response SHALL include an array of packages each containing: tracking_id, vendor, name, status, delivered flag, events array, estimated_delivery, last_location, last_event_time

### Requirement: Add package command

The integration SHALL expose a WebSocket command `paketti_tracker/add_package` accepting tracking_id (string), vendor (string), and name (optional string).

#### Scenario: Successful add
- **WHEN** the panel sends `paketti_tracker/add_package` with valid data
- **THEN** the package SHALL be added to the config entry options and coordinator SHALL refresh

#### Scenario: Duplicate rejected
- **WHEN** the panel sends `paketti_tracker/add_package` with an already-tracked ID
- **THEN** the response SHALL return an error with code "already_tracked"

### Requirement: Remove package command

The integration SHALL expose a WebSocket command `paketti_tracker/remove_package` accepting tracking_id (string).

#### Scenario: Successful remove
- **WHEN** the panel sends `paketti_tracker/remove_package` with an existing tracking ID
- **THEN** the package SHALL be removed from config entry options and its entity removed

#### Scenario: Not found
- **WHEN** the panel sends `paketti_tracker/remove_package` with an unknown tracking ID
- **THEN** the response SHALL return an error with code "not_found"

### Requirement: Refresh command

The integration SHALL expose a WebSocket command `paketti_tracker/refresh` that triggers an immediate coordinator update.

#### Scenario: Refresh triggers update
- **WHEN** the panel sends `paketti_tracker/refresh`
- **THEN** the coordinator SHALL immediately fetch fresh data and the response SHALL return the updated package list

### Requirement: Settings commands

The integration SHALL expose `paketti_tracker/get_settings` and `paketti_tracker/update_settings` WebSocket commands for reading and modifying the poll interval.

#### Scenario: Get settings
- **WHEN** the panel sends `paketti_tracker/get_settings`
- **THEN** the response SHALL include `poll_interval_minutes` (integer)

#### Scenario: Update poll interval
- **WHEN** the panel sends `paketti_tracker/update_settings` with `poll_interval_minutes: 30`
- **THEN** the coordinator's update interval SHALL change to 30 minutes
