## ADDED Requirements

### Requirement: Vertical event timeline

Each package card SHALL have an expandable delivery timeline showing all tracking events in reverse chronological order as a vertical stepper.

#### Scenario: Timeline displays events
- **WHEN** user expands a package card
- **THEN** the timeline SHALL show each event with: timestamp (formatted), city/location, event description, and a connecting vertical line between events

#### Scenario: Status-colored timeline nodes
- **WHEN** events are rendered in the timeline
- **THEN** each node SHALL be color-coded: green for delivered/pickup-ready events, blue for in-transit, gray for pending, red for exceptions

#### Scenario: Empty timeline
- **WHEN** a package has no events yet
- **THEN** the timeline SHALL show a single "Awaiting first scan" placeholder node

### Requirement: Current status indicator

The timeline SHALL visually highlight the current/most-recent event as the active state.

#### Scenario: Active event highlighted
- **WHEN** the timeline is displayed
- **THEN** the most recent event node SHALL be larger/bolder than past events to indicate it is the current state
