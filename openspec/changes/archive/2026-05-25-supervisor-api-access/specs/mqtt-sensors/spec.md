## MODIFIED Requirements

### Requirement: MQTT broker connection

The system SHALL connect to the MQTT broker using host, port, username, and password obtained from the Supervisor services API (`GET http://supervisor/services/mqtt` with `Authorization: Bearer ${SUPERVISOR_TOKEN}`). The add-on manifest SHALL declare `hassio_api: true` and `services: [mqtt]` to ensure access is granted.

#### Scenario: Successful connection with Supervisor credentials
- **WHEN** the add-on starts and the Supervisor services API returns MQTT configuration
- **THEN** it SHALL use the provided host, port, username, and password to connect

#### Scenario: Supervisor API returns 403 without hassio_api
- **WHEN** the add-on manifest lacks `hassio_api: true`
- **THEN** the Supervisor SHALL reject the API call with 403 Forbidden

#### Scenario: Supervisor API succeeds with hassio_api declared
- **WHEN** the add-on manifest includes `hassio_api: true` and `services: [mqtt]`
- **THEN** the Supervisor SHALL return MQTT credentials from the services API
