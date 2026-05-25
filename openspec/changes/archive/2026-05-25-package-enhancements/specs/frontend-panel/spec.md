## REMOVED Requirements

### Requirement: Event location map
**Reason**: Map adds bundle size (~100KB) and Nominatim geocoding complexity for minimal user value. Users primarily care about status progression (timeline), not geographic routing.
**Migration**: No migration needed. Map has no persistent state. Timeline remains as the primary detail view.

### Requirement: Geocoding with caching
**Reason**: Removed along with event map. Geocoding was only used for the map visualization.
**Migration**: No migration needed. Cached geocoding data in localStorage will be orphaned but harmless.

## MODIFIED Requirements

### Requirement: Panel sidebar with package management

The integration SHALL register a sidebar panel at `/paketti-tracker` providing a visual interface for package management including: package list with status, delivery timeline, add/remove/edit packages, notification settings, and email configuration.

#### Scenario: Panel shows all tracked packages
- **WHEN** the user opens the Paketti Tracker panel
- **THEN** all tracked packages SHALL be displayed as cards with status, name, tracking ID, carrier, last event, and last updated time

#### Scenario: Edit package from panel
- **WHEN** the user clicks the edit button on a package card
- **THEN** an edit dialog SHALL open allowing the user to change the package name and carrier

#### Scenario: Last updated displayed
- **WHEN** a package card is rendered
- **THEN** it SHALL show the relative time since last data fetch (e.g. "5 min ago")

#### Scenario: Notification settings in drawer
- **WHEN** the user opens the settings drawer
- **THEN** it SHALL include a notifications section with trigger checkboxes and device selection

#### Scenario: Email settings in drawer
- **WHEN** the user opens the settings drawer
- **THEN** it SHALL include an email section with IMAP configuration, test button, and auto-add toggle

#### Scenario: Discovered packages shown
- **WHEN** there are packages discovered from email but not yet confirmed
- **THEN** they SHALL be shown in a separate "Discovered" section with confirm/dismiss actions

#### Scenario: Carrier tracking link
- **WHEN** a package card is rendered
- **THEN** it SHALL include a link/button that opens the package's tracking page on the carrier's website in a new tab
