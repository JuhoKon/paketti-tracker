## ADDED Requirements

### Requirement: MQTT broker connection

The system SHALL connect to the MQTT broker using host, port, username, and password obtained from Supervisor API or add-on options.

#### Scenario: Successful connection
- **WHEN** the add-on starts with valid MQTT credentials
- **THEN** it SHALL establish a persistent connection to the MQTT broker

#### Scenario: Connection failure
- **WHEN** MQTT credentials are invalid or broker is unreachable
- **THEN** the system SHALL log a warning and retry with backoff without crashing

---

### Requirement: Discovery config publishing

The system SHALL publish MQTT discovery configuration for each tracked package to homeassistant/sensor/paketti_tracker_{id}/config.

#### Scenario: Discovery published on package add
- **WHEN** a new package is added to tracking
- **THEN** a discovery config payload SHALL be published containing name, state_topic, unique_id, device info, and json_attributes_topic

#### Scenario: Discovery payload structure
- **WHEN** discovery config is published
- **THEN** the payload SHALL include device block with identifier "paketti_tracker" grouping all sensors under a single "Paketti Tracker" device

---

### Requirement: State and attribute publishing

The system SHALL publish state updates to paketti_tracker/{tracking_id}/state and attributes to paketti_tracker/{tracking_id}/attributes.

#### Scenario: State update on poll
- **WHEN** a package status is updated by the scraper
- **THEN** the status string SHALL be published to the state topic

#### Scenario: Attributes published
- **WHEN** a package is updated
- **THEN** a JSON payload with vendor, name, events, estimated_delivery, and last_location SHALL be published to the attributes topic

---

### Requirement: Availability topic

The system SHALL set an availability topic and publish online on connect and offline on graceful disconnect.

#### Scenario: Online on connect
- **WHEN** the MQTT client connects to the broker
- **THEN** it SHALL publish "online" to the availability topic

#### Scenario: Offline on disconnect
- **WHEN** the add-on shuts down gracefully
- **THEN** it SHALL publish "offline" to the availability topic (or use LWT)

---

### Requirement: Discovery removal on package delete

The system SHALL remove the discovery config by publishing an empty payload when a package is removed.

#### Scenario: Package removed
- **WHEN** a user deletes a tracked package
- **THEN** an empty payload SHALL be published to homeassistant/sensor/paketti_tracker_{id}/config

---

### Requirement: Republish on reconnect

The system SHALL republish all sensor discovery configs and current states upon reconnecting to the broker.

#### Scenario: Broker reconnect
- **WHEN** the MQTT connection is re-established after a disconnection
- **THEN** all discovery configs and current states SHALL be republished
