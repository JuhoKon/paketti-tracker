## MODIFIED Requirements

### Requirement: Ingress SPA replacing HA panel

The frontend SHALL be served as an ingress SPA (Single Page Application) accessed through the HA add-on panel, communicating with the backend via REST API (fetch/axios) instead of HA WebSocket commands. Asset references SHALL use relative paths (`./assets/...`) so they resolve correctly through the ingress proxy.

#### Scenario: User accesses frontend
- **WHEN** the user opens the Paketti Tracker add-on in HA
- **THEN** the ingress proxy SHALL serve the SPA at the add-on's ingress URL

#### Scenario: API communication via REST
- **WHEN** the frontend needs to fetch or mutate data
- **THEN** it SHALL use HTTP requests (fetch/axios) to the REST API endpoints, not HA WebSocket

#### Scenario: Assets load through ingress
- **WHEN** the browser loads index.html through ingress at /api/hassio_ingress/<token>/
- **THEN** CSS and JS assets SHALL be referenced with relative paths (./assets/...)
- **AND** the browser SHALL request assets through the same ingress path

---

## ADDED Requirements

### Requirement: Static file MIME types

The backend SHALL serve static frontend files with correct Content-Type headers based on file extension.

#### Scenario: CSS file served with correct MIME type
- **WHEN** the browser requests a .css file from the add-on
- **THEN** the response SHALL have Content-Type: text/css

#### Scenario: JavaScript file served with correct MIME type
- **WHEN** the browser requests a .js file from the add-on
- **THEN** the response SHALL have Content-Type: application/javascript

### Requirement: Vite relative base path

The Vite build configuration SHALL set `base: "./"` to produce relative asset references in the built HTML.

#### Scenario: Built HTML contains relative paths
- **WHEN** `npm run build` completes
- **THEN** the generated index.html SHALL reference scripts as `./assets/index-*.js`
- **AND** SHALL reference stylesheets as `./assets/index-*.css`
