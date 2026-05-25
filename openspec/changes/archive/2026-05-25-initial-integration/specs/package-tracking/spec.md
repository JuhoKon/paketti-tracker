## ADDED Requirements

### Requirement: Normalized status vocabulary
The integration SHALL map all carrier-specific status strings to a fixed set of normalized values: `pending`, `in_transit`, `out_for_delivery`, `delivered`, `exception`, `unknown`. No raw carrier string SHALL appear as a sensor state.

#### Scenario: Known carrier status mapped to normalized value
- **WHEN** a scraper returns a carrier-specific status string that matches a known mapping
- **THEN** the sensor state SHALL be set to the corresponding normalized value

#### Scenario: Unknown carrier status handled gracefully
- **WHEN** a scraper returns a status string that has no known mapping
- **THEN** the sensor state SHALL be set to `unknown`

---

### Requirement: Sensor entity per package
The integration SHALL create exactly one `SensorEntity` per tracked package. The entity state SHALL reflect the current normalized status.

#### Scenario: Entity created for new package
- **WHEN** a package is added to the integration
- **THEN** a sensor entity SHALL be created with a unique `entity_id` derived from the vendor and tracking ID

#### Scenario: Entity friendly name uses nickname when set
- **WHEN** a package has an optional name set by the user
- **THEN** the entity's `friendly_name` SHALL display that name

#### Scenario: Entity friendly name falls back to tracking ID
- **WHEN** a package has no name set
- **THEN** the entity's `friendly_name` SHALL display the tracking ID

---

### Requirement: Sensor attributes
Each sensor entity SHALL expose the following attributes: `vendor`, `tracking_id`, `name`, `estimated_delivery`, `last_location`, `last_event_time`, `events` (last 10 events as a list), `delivered` (boolean).

#### Scenario: Attributes populated after successful scrape
- **WHEN** the coordinator successfully retrieves tracking data for a package
- **THEN** all attributes SHALL be populated with the latest data from the scraper result

#### Scenario: Events list capped at ten entries
- **WHEN** a carrier returns more than ten tracking events
- **THEN** the `events` attribute SHALL contain only the ten most recent events

#### Scenario: Missing optional attributes handled gracefully
- **WHEN** a carrier does not provide an estimated delivery date
- **THEN** the `estimated_delivery` attribute SHALL be `null`

---

### Requirement: Hourly polling
The coordinator SHALL poll all non-delivered packages once per hour.

#### Scenario: Coordinator schedules regular updates
- **WHEN** the integration is loaded
- **THEN** the coordinator SHALL schedule polling at a 60-minute interval

#### Scenario: Delivered packages skipped
- **WHEN** a package has status `delivered` in the coordinator's last known data
- **THEN** the coordinator SHALL NOT issue a scrape request for that package in subsequent polling cycles

---

### Requirement: Scrape failure surfaces as unavailable
If a scraper raises an error for a package, the corresponding sensor SHALL become `unavailable`. It SHALL NOT display the last known state as if it were current.

#### Scenario: Scrape failure marks entity unavailable
- **WHEN** a scraper raises a `ScraperError` for a given tracking ID
- **THEN** the sensor entity for that package SHALL have state `unavailable`

#### Scenario: Other packages unaffected by single scrape failure
- **WHEN** one scraper fails for one package
- **THEN** all other sensor entities SHALL continue updating normally

---

### Requirement: State history via HA recorder
Package status history SHALL be preserved automatically through HA's built-in recorder. No custom storage mechanism is needed.

#### Scenario: State change recorded by HA
- **WHEN** a package status transitions (e.g., `in_transit` → `out_for_delivery`)
- **THEN** HA's recorder SHALL log the state change with its timestamp
