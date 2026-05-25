## MODIFIED Requirements

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

The add-on SHALL provide a config.yaml defining metadata including name, version, supported architectures, ingress configuration, exposed ports, configurable options, and `init: false` to prevent Docker init process injection.

#### Scenario: Supervisor reads config.yaml
- **WHEN** the add-on is installed
- **THEN** Supervisor SHALL parse config.yaml with name, version, arch list, ingress: true, ingress_port: 8099, init: false, and options schema

---

## ADDED Requirements

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
