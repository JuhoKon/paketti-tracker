## MODIFIED Requirements

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
