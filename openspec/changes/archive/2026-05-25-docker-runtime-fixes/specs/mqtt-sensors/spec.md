## MODIFIED Requirements

### Requirement: MQTT broker connection

The system SHALL connect to the MQTT broker using host, port, username, and password obtained from the Supervisor services API (`GET http://supervisor/services/mqtt` with `Authorization: Bearer ${SUPERVISOR_TOKEN}`). If the API is unavailable, it SHALL fall back to `core-mosquitto:1883` with no credentials.

#### Scenario: Successful connection with Supervisor credentials
- **WHEN** the add-on starts and the Supervisor services API returns MQTT configuration
- **THEN** it SHALL use the provided host, port, username, and password to connect

#### Scenario: Supervisor API unavailable
- **WHEN** the Supervisor services API fails or returns no MQTT service
- **THEN** the system SHALL fall back to host=core-mosquitto, port=1883, no auth
- **AND** SHALL log a warning about missing MQTT credentials

#### Scenario: Connection failure with auth
- **WHEN** MQTT credentials from Supervisor are invalid
- **THEN** the system SHALL log a warning with the error code and retry with backoff without crashing

#### Scenario: Credentials refreshed on reconnect
- **WHEN** the MQTT connection is lost and a reconnect is attempted
- **THEN** the system SHALL re-fetch credentials from the Supervisor API before reconnecting
