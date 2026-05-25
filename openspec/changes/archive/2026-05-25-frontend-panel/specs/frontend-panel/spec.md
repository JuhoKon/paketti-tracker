## ADDED Requirements

### Requirement: Panel appears in HA sidebar

The integration SHALL register a custom panel accessible from the HA sidebar with title "Paketti Tracker" and icon `mdi:package-variant`.

#### Scenario: Panel visible after integration setup
- **WHEN** the Paketti Tracker integration is configured
- **THEN** a "Paketti Tracker" entry SHALL appear in the HA sidebar navigation

#### Scenario: Panel loads without error
- **WHEN** user clicks the "Paketti Tracker" sidebar entry
- **THEN** the panel SHALL load and display the package list view

### Requirement: Package list view

The panel SHALL display all tracked packages as cards showing: package name, tracking ID, carrier, status badge (color-coded), and most recent event summary.

#### Scenario: Packages displayed
- **WHEN** the panel loads with configured packages
- **THEN** each package SHALL be shown as a card with name, tracking ID, carrier name, colored status badge, and last event description with timestamp

#### Scenario: Empty state
- **WHEN** no packages are configured
- **THEN** the panel SHALL display a friendly empty state message with a prominent "Add Package" button

### Requirement: Add package from panel

The panel SHALL provide a dialog to add a new package with fields: tracking ID (required), carrier (select, required), and name (optional).

#### Scenario: Successful add
- **WHEN** user fills in a valid tracking ID and carrier and submits
- **THEN** the package SHALL be added to tracking and appear in the list immediately

#### Scenario: Duplicate tracking ID
- **WHEN** user enters a tracking ID that is already tracked
- **THEN** the dialog SHALL show an error and not add the duplicate

### Requirement: Remove package from panel

The panel SHALL allow removing packages from the list.

#### Scenario: Remove via card action
- **WHEN** user clicks the remove/delete action on a package card
- **THEN** a confirmation prompt SHALL appear, and on confirm the package SHALL be removed from tracking

### Requirement: Manual refresh

The panel SHALL have a refresh button that triggers an immediate data update for all packages.

#### Scenario: Refresh updates data
- **WHEN** user clicks the refresh button
- **THEN** the coordinator SHALL fetch fresh data for all non-delivered packages and the UI SHALL update with new results

### Requirement: Settings panel

The panel SHALL provide a settings section where users can configure the poll interval.

#### Scenario: Change poll interval
- **WHEN** user changes the poll interval in settings
- **THEN** the coordinator SHALL use the new interval for subsequent updates

### Requirement: HA Material Design styling

The panel SHALL follow HA's Material Design conventions using HA color tokens (CSS custom properties), standard spacing, and typography consistent with the native HA interface.

#### Scenario: Visual consistency
- **WHEN** the panel is displayed
- **THEN** it SHALL use `--primary-color`, `--card-background-color`, `--primary-text-color` and other HA CSS tokens for theming
