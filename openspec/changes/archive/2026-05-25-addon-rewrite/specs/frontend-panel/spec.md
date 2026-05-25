## MODIFIED Requirements

### Requirement: Ingress SPA replacing HA panel

The frontend SHALL be served as an ingress SPA (Single Page Application) accessed through the HA add-on panel, communicating with the backend via REST API (fetch/axios) instead of HA WebSocket commands.

#### Scenario: User accesses frontend
- **WHEN** the user opens the Paketti Tracker add-on in HA
- **THEN** the ingress proxy SHALL serve the SPA at the add-on's ingress URL

#### Scenario: API communication via REST
- **WHEN** the frontend needs to fetch or mutate data
- **THEN** it SHALL use HTTP requests (fetch/axios) to the REST API endpoints, not HA WebSocket

---

### Requirement: SPA routing

The frontend SHALL use React Router for client-side routing with pages for dashboard (package list) and settings.

#### Scenario: Navigate between pages
- **WHEN** the user clicks a navigation link
- **THEN** the SPA SHALL route client-side without full page reload

#### Scenario: Direct URL access
- **WHEN** a user navigates directly to a sub-route (e.g. /settings)
- **THEN** the server SHALL serve the SPA index and React Router SHALL handle the route

---

### Requirement: No single-file IIFE constraint

The frontend build SHALL NOT be constrained to a single IIFE file. Standard bundling (multiple chunks, code splitting) is permitted.

#### Scenario: Build output
- **WHEN** the frontend is built for production
- **THEN** the output MAY contain multiple JS/CSS files with standard chunk splitting

---

### Requirement: Material Design styling

The frontend SHALL use Material Design styling compatible with Home Assistant themes.

#### Scenario: Visual consistency
- **WHEN** the frontend is rendered within the HA ingress frame
- **THEN** it SHALL use Material Design components and colors consistent with HA's visual style

---

### Requirement: Panel sidebar with package management

The frontend SHALL provide a visual interface for package management including: package list with status, delivery timeline, add/remove/edit packages, notification settings, and email configuration.

#### Scenario: Panel shows all tracked packages
- **WHEN** the user opens the Paketti Tracker panel
- **THEN** all tracked packages SHALL be displayed as cards with status, name, tracking ID, carrier, last event, and last updated time

#### Scenario: Edit package from panel
- **WHEN** the user clicks the edit button on a package card
- **THEN** an edit dialog SHALL open allowing the user to change the package name and carrier

#### Scenario: Notification settings in settings page
- **WHEN** the user navigates to the settings page
- **THEN** it SHALL include a notifications section with trigger checkboxes and device selection

#### Scenario: Email settings in settings page
- **WHEN** the user navigates to the settings page
- **THEN** it SHALL include an email section with IMAP configuration, test button, and auto-add toggle

#### Scenario: Discovered packages shown
- **WHEN** there are packages discovered from email but not yet confirmed
- **THEN** they SHALL be shown in a separate "Discovered" section with confirm/dismiss actions

#### Scenario: Carrier tracking link
- **WHEN** a package card is rendered
- **THEN** it SHALL include a link/button that opens the package's tracking page on the carrier's website in a new tab

## REMOVED Requirements

### Requirement: HA panel_custom registration
**Reason**: The frontend is now served via ingress, not registered as a panel_custom element.
**Migration**: Users access the UI through the add-on panel instead of a sidebar item.
