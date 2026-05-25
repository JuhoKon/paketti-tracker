## ADDED Requirements

### Requirement: Event location map

Each package card SHALL include a map view showing the geographic locations of tracking events plotted on OpenStreetMap tiles via Leaflet.

#### Scenario: Map shows event cities
- **WHEN** user expands the map for a package
- **THEN** the map SHALL display markers for each event that has a resolvable city, connected by a line showing the route

#### Scenario: Map handles unresolvable locations
- **WHEN** an event city cannot be geocoded
- **THEN** that event SHALL be skipped on the map without error and remaining events SHALL still display

#### Scenario: Map lazy-loaded
- **WHEN** the panel initially loads
- **THEN** Leaflet SHALL NOT be loaded until a user expands a package's map view (to reduce initial bundle size)

### Requirement: Geocoding with caching

City names from tracking events SHALL be geocoded using Nominatim (OpenStreetMap) and cached to avoid repeated lookups.

#### Scenario: City geocoded and cached
- **WHEN** a new city name appears in tracking events
- **THEN** it SHALL be geocoded once via Nominatim and the result cached for future use

#### Scenario: Rate limiting respected
- **WHEN** multiple cities need geocoding
- **THEN** requests SHALL be spaced at minimum 1 second apart to respect Nominatim usage policy
