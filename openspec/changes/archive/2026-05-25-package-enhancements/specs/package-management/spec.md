## MODIFIED Requirements

### Requirement: Package add/remove via WebSocket

The system SHALL support adding, removing, and editing packages via WebSocket commands. Both WS commands and the existing options flow SHALL modify the same underlying config entry options and trigger coordinator refresh.

#### Scenario: Add via WebSocket updates options
- **WHEN** a package is added via `paketti_tracker/add_package` WebSocket command
- **THEN** the config entry options SHALL be updated with the new package and the coordinator SHALL refresh

#### Scenario: Remove via WebSocket updates options
- **WHEN** a package is removed via `paketti_tracker/remove_package` WebSocket command
- **THEN** the config entry options SHALL be updated without the removed package and the entity SHALL be removed

#### Scenario: Edit via WebSocket updates options
- **WHEN** a package is edited via `paketti_tracker/edit_package` with a new name or vendor
- **THEN** the config entry options SHALL be updated in-place and the coordinator SHALL refresh

#### Scenario: Edit non-existent package
- **WHEN** `paketti_tracker/edit_package` is called with an unknown tracking ID
- **THEN** the response SHALL return an error with code "not_found"

#### Scenario: Options flow still works
- **WHEN** a user adds/removes packages via Settings → Integrations → Configure
- **THEN** the existing options flow SHALL continue to work as before

## ADDED Requirements

### Requirement: Last updated timestamp per package

Each package's tracking data SHALL include a `last_updated` timestamp indicating when the carrier data was last successfully fetched.

#### Scenario: Last updated set on fetch
- **WHEN** the coordinator successfully fetches tracking data for a package
- **THEN** `last_updated` SHALL be set to the current UTC time

#### Scenario: Last updated preserved for delivered packages
- **WHEN** a delivered package is skipped during polling
- **THEN** `last_updated` SHALL retain the timestamp from the last successful fetch

#### Scenario: Last updated preserved on error
- **WHEN** a fetch fails and previous data is preserved
- **THEN** `last_updated` SHALL retain the previous value (not be updated to current time)

### Requirement: Carrier tracking URL per package

Each package SHALL expose a `tracking_url` linking to the carrier's public tracking page for that tracking ID.

#### Scenario: Posti tracking URL
- **WHEN** a package has vendor `posti` and tracking ID `JJFI12345600001234`
- **THEN** `tracking_url` SHALL be `https://www.posti.fi/fi/seuranta#/lahetys/JJFI12345600001234`

#### Scenario: Postnord tracking URL
- **WHEN** a package has vendor `postnord` and tracking ID `12345`
- **THEN** `tracking_url` SHALL be `https://tracking.postnord.com/fi/?id=12345`

#### Scenario: Matkahuolto tracking URL
- **WHEN** a package has vendor `matkahuolto` and tracking ID `ABC123`
- **THEN** `tracking_url` SHALL be `https://www.matkahuolto.fi/seuranta/tilaus/ABC123`

#### Scenario: Tracking URL included in WS response
- **WHEN** the panel requests `paketti_tracker/packages`
- **THEN** each package object in the response SHALL include a `tracking_url` field
