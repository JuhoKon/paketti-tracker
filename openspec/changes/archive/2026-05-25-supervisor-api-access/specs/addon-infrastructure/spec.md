## MODIFIED Requirements

### Requirement: Add-on manifest configuration

The add-on SHALL provide a config.yaml defining metadata including name, version, supported architectures, ingress configuration, exposed ports, configurable options (including email IMAP settings), `init: false`, `hassio_api: true`, `homeassistant_api: true`, and `services: [mqtt]`.

#### Scenario: Supervisor grants API access
- **WHEN** the add-on starts
- **THEN** `hassio_api: true` SHALL allow the add-on to call `http://supervisor/*` endpoints (including `/services/mqtt`)
- **AND** `homeassistant_api: true` SHALL allow the add-on to call `http://supervisor/core/api/*` endpoints (notify services)

#### Scenario: MQTT service dependency declared
- **WHEN** the add-on is installed
- **THEN** `services: [mqtt]` SHALL tell Supervisor this add-on requires the MQTT broker
- **AND** Supervisor SHALL ensure Mosquitto is available before starting the add-on

#### Scenario: Supervisor reads config.yaml
- **WHEN** the add-on is installed or options are changed
- **THEN** Supervisor SHALL parse config.yaml with all declared fields including hassio_api, homeassistant_api, and services
