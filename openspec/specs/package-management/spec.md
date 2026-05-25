## ADDED Requirements

### Requirement: Add package via options flow
A user SHALL be able to add a tracked package by opening the integration's options flow and providing a tracking ID, a vendor, and an optional name.

#### Scenario: Package added with all fields
- **WHEN** the user completes the add-package step with a tracking ID, vendor, and name
- **THEN** the package SHALL be persisted in the config entry options and a corresponding sensor entity SHALL be created

#### Scenario: Package added without optional name
- **WHEN** the user completes the add-package step with only a tracking ID and vendor
- **THEN** the package SHALL be persisted with no name and the sensor entity SHALL use the tracking ID as its friendly name

#### Scenario: Duplicate tracking ID rejected
- **WHEN** the user attempts to add a tracking ID that is already tracked
- **THEN** the options flow SHALL display a validation error and SHALL NOT add a duplicate entry

---

### Requirement: Remove package via options flow
A user SHALL be able to remove one or more tracked packages by opening the integration's options flow and selecting packages to delete.

#### Scenario: Package removed by user
- **WHEN** the user selects a package in the remove step and confirms
- **THEN** the package SHALL be removed from the config entry options and its sensor entity SHALL be removed from HA

#### Scenario: Multiple packages removed in one flow run
- **WHEN** the user selects multiple packages in the remove step
- **THEN** all selected packages SHALL be removed

---

### Requirement: Package list persisted across restarts
The list of tracked packages SHALL be stored in the config entry options so that it survives HA restarts and config entry reloads.

#### Scenario: Packages survive restart
- **WHEN** HA is restarted
- **THEN** all previously added packages SHALL still be tracked and their entities SHALL be recreated

---

### Requirement: Delivered entities persist until removed
A sensor entity for a delivered package SHALL remain in HA until the user explicitly removes it via the options flow.

#### Scenario: Delivered package entity not auto-removed
- **WHEN** a package transitions to `delivered`
- **THEN** the sensor entity SHALL remain with state `delivered` and SHALL NOT be removed automatically

#### Scenario: User removes delivered package
- **WHEN** the user removes a delivered package via the options flow
- **THEN** the entity SHALL be removed from HA

---

### Requirement: Package add/remove via WebSocket

The system SHALL support adding and removing packages via WebSocket commands in addition to the existing options flow. Both methods SHALL modify the same underlying config entry options and trigger coordinator refresh.

#### Scenario: Add via WebSocket updates options
- **WHEN** a package is added via `paketti_tracker/add_package` WebSocket command
- **THEN** the config entry options SHALL be updated with the new package and the coordinator SHALL refresh

#### Scenario: Remove via WebSocket updates options
- **WHEN** a package is removed via `paketti_tracker/remove_package` WebSocket command
- **THEN** the config entry options SHALL be updated without the removed package and the entity SHALL be removed

#### Scenario: Options flow still works
- **WHEN** a user adds/removes packages via Settings → Integrations → Configure
- **THEN** the existing options flow SHALL continue to work as before
