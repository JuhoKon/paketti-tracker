## ADDED Requirements

### Requirement: Scraper polling task

The scheduler SHALL run a scraper polling task on a configurable interval (default 60 minutes) that fetches updates for all non-delivered packages.

#### Scenario: Polling runs on interval
- **WHEN** the configured poll interval elapses
- **THEN** the scraper SHALL poll all active (non-delivered) packages

#### Scenario: Delivered packages skipped
- **WHEN** a package has status delivered
- **THEN** it SHALL NOT be included in the polling cycle

---

### Requirement: Email polling task

The scheduler SHALL run an email polling task on a configurable interval (default 30 minutes) that checks for new tracking numbers in email.

#### Scenario: Email poll runs on interval
- **WHEN** the email poll interval elapses
- **THEN** the email parser SHALL check for new tracking numbers

---

### Requirement: Lifespan management

Scheduled tasks SHALL start with the application lifespan and stop cleanly on shutdown.

#### Scenario: Tasks start on app startup
- **WHEN** the FastAPI application starts
- **THEN** all scheduled tasks SHALL be registered and running

#### Scenario: Clean shutdown
- **WHEN** the application receives a shutdown signal
- **THEN** all running tasks SHALL be cancelled and awaited cleanly

---

### Requirement: Dynamic interval changes

Interval changes SHALL take effect on the next polling cycle without requiring a restart.

#### Scenario: Interval updated via API
- **WHEN** the user changes the poll interval via PATCH /api/settings
- **THEN** the next polling cycle SHALL use the new interval

---

### Requirement: Initial poll on startup

An initial poll SHALL run immediately on startup after a 5-second delay to allow the system to stabilize.

#### Scenario: Startup poll
- **WHEN** the application finishes initialization
- **THEN** a scraper poll SHALL execute after a 5-second delay

---

### Requirement: Error isolation

Errors in polling one package SHALL NOT prevent polling of other packages.

#### Scenario: One package errors
- **WHEN** the scraper fails for one package during a polling cycle
- **THEN** the remaining packages SHALL still be polled successfully

---

### Requirement: Polling result logging

The scheduler SHALL log polling results including success count and error count after each cycle.

#### Scenario: Cycle completes
- **WHEN** a polling cycle finishes
- **THEN** a log entry SHALL be written with the number of successful and failed polls
