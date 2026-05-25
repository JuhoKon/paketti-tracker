## ADDED Requirements

### Requirement: Docker container runtime

The add-on container SHALL use a multi-stage Docker build: stage 1 builds the React frontend with Node.js, stage 2 runs Python 3.12 with FastAPI and uvicorn as the application server. A build.yaml SHALL map each supported architecture (aarch64, amd64, armv7) to the correct HA base image via the BUILD_FROM arg.

#### Scenario: Container starts successfully
- **WHEN** the add-on is started by HA Supervisor
- **THEN** uvicorn SHALL start the FastAPI application on port 8099

#### Scenario: Frontend is built during Docker build
- **WHEN** the Docker image is built
- **THEN** stage 1 SHALL run `npm ci && npm run build` producing frontend/dist/
- **AND** stage 2 SHALL COPY the built assets from stage 1

#### Scenario: Multi-arch build
- **WHEN** the add-on is built for aarch64
- **THEN** Supervisor SHALL pass the aarch64-base-python image as BUILD_FROM

---

### Requirement: Add-on manifest configuration

The add-on SHALL provide a config.yaml defining metadata including name, version, supported architectures, ingress configuration, exposed ports, and configurable options.

#### Scenario: Supervisor reads config.yaml
- **WHEN** the add-on is installed
- **THEN** Supervisor SHALL parse config.yaml with name, version, arch list, ingress: true, ingress_port: 8099, and options schema

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
