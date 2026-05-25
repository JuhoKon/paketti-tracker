## ADDED Requirements

### Requirement: Docker container runtime

The add-on container SHALL use a multi-stage Docker build: stage 1 builds the React frontend with Node.js, stage 2 runs Python 3.12 with FastAPI and uvicorn as the application server. The BUILD_FROM arg SHALL be declared before any FROM instruction and default to the aarch64 base image. Supervisor passes the correct architecture-specific image via `--build-arg`.

#### Scenario: Container starts successfully
- **WHEN** the add-on is started by HA Supervisor
- **THEN** uvicorn SHALL start the FastAPI application on port 8099

#### Scenario: Frontend is built during Docker build
- **WHEN** the Docker image is built
- **THEN** stage 1 SHALL run `npm ci && npm run build` producing frontend/dist/
- **AND** stage 2 SHALL COPY the built assets from stage 1

#### Scenario: Multi-arch build
- **WHEN** the add-on is built for aarch64
- **THEN** Supervisor SHALL pass the aarch64-base-python image as BUILD_FROM via --build-arg

#### Scenario: s6-overlay runs as PID 1
- **WHEN** the container starts
- **THEN** s6-overlay `/init` SHALL be PID 1 (config.yaml sets `init: false` to prevent tini injection)

#### Scenario: Service working directory
- **WHEN** the s6 service script runs
- **THEN** it SHALL change to `/app` before executing uvicorn (s6 services start in `/`)

---

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

#### Scenario: Supervisor reads config.yaml with email options
- **WHEN** the add-on is installed or options are changed
- **THEN** Supervisor SHALL parse config.yaml with email options: email_enabled (bool), email_host (str), email_port (int), email_username (str), email_password (password), email_folder (str), email_auto_add (bool)

#### Scenario: Email options have sensible defaults
- **WHEN** the add-on is installed without user customization
- **THEN** email_enabled SHALL default to false
- **AND** email_host SHALL default to empty string
- **AND** email_port SHALL default to 993
- **AND** email_username SHALL default to empty string
- **AND** email_password SHALL default to empty string
- **AND** email_folder SHALL default to "INBOX"
- **AND** email_auto_add SHALL default to false

#### Scenario: Password masked in HA UI
- **WHEN** the user views add-on options in HA
- **THEN** the email_password field SHALL be displayed as a password (masked) input

---

### Requirement: Ingress proxy

The add-on SHALL expose port 8099 internally and enable ingress so that HA proxies requests to the add-on UI.

#### Scenario: User accesses add-on via ingress
- **WHEN** a user navigates to the add-on panel in HA
- **THEN** HA SHALL proxy the request to port 8099 on the add-on container

---

### Requirement: Health endpoint

The add-on SHALL expose a health endpoint at /api/health that returns HTTP 200 when the application is ready to serve requests.

#### Scenario: Health check succeeds
- **WHEN** a GET request is made to /api/health after startup completes
- **THEN** the response SHALL be HTTP 200 with a JSON body indicating healthy status

#### Scenario: Health check during startup
- **WHEN** a GET request is made to /api/health before the app is fully initialized
- **THEN** the response SHALL be HTTP 503

---

### Requirement: Persistent data directory

All persistent data SHALL be stored in the /data/ directory which is mapped by Supervisor across add-on restarts and updates.

#### Scenario: Data survives restart
- **WHEN** the add-on is restarted
- **THEN** all files in /data/ SHALL be preserved

---

### Requirement: Environment variables

The add-on SHALL have access to SUPERVISOR_TOKEN and MQTT broker connection details via environment variables provided by Supervisor.

#### Scenario: Supervisor token available
- **WHEN** the add-on starts
- **THEN** the SUPERVISOR_TOKEN environment variable SHALL be set and valid for HA REST API calls

#### Scenario: MQTT details available
- **WHEN** the add-on starts with MQTT configured in HA
- **THEN** MQTT host, port, username, and password SHALL be available via Supervisor API or environment variables

---

### Requirement: Configuration null value handling

The run.sh entry script SHALL handle bashio returning the literal string "null" for unconfigured options by filtering these values and applying sensible defaults.

#### Scenario: bashio returns null for poll interval
- **WHEN** bashio::config returns "null" for poll_interval_minutes
- **THEN** run.sh SHALL export PAKETTI_POLL_INTERVAL with default value 60

#### Scenario: bashio returns null for log level
- **WHEN** bashio::config returns "null" for log_level
- **THEN** run.sh SHALL export PAKETTI_LOG_LEVEL with default value "info"

#### Scenario: Invalid log level rejected
- **WHEN** the log level value is not one of debug, info, warning, error, critical
- **THEN** run.sh SHALL fall back to "info"
