## ADDED Requirements

### Requirement: SQLite storage location

The database SHALL be stored at /data/paketti_tracker.db so that it persists across add-on restarts.

#### Scenario: Database created on first run
- **WHEN** the add-on starts and no database file exists at /data/paketti_tracker.db
- **THEN** the system SHALL create the database and initialize the schema

#### Scenario: Database preserved on restart
- **WHEN** the add-on restarts
- **THEN** the existing database at /data/paketti_tracker.db SHALL be reused with all data intact

---

### Requirement: Packages table schema

The packages table SHALL contain columns: tracking_id (TEXT, PK), vendor (TEXT), name (TEXT), status (TEXT), delivered (BOOLEAN), last_updated (DATETIME), tracking_url (TEXT), estimated_delivery (DATE), last_location (TEXT), last_event_time (DATETIME), created_at (DATETIME).

#### Scenario: Store a new package
- **WHEN** a package is inserted into the packages table
- **THEN** all required fields SHALL be stored and retrievable by tracking_id

---

### Requirement: Tracking events table schema

The tracking_events table SHALL contain columns: id (INTEGER, PK, autoincrement), tracking_id (TEXT, FK to packages), timestamp (DATETIME), description (TEXT), location (TEXT).

#### Scenario: Store tracking events
- **WHEN** new events are fetched for a package
- **THEN** each event SHALL be inserted with its timestamp, description, and location

#### Scenario: Foreign key cascade on package delete
- **WHEN** a package is deleted from the packages table
- **THEN** all associated tracking_events SHALL be deleted

---

### Requirement: Settings table schema

The settings table SHALL be a key-value store with columns: key (TEXT, PK), value (TEXT/JSON) storing poll_interval, notification config, and email config.

#### Scenario: Read default settings
- **WHEN** a setting key is queried that has not been explicitly set
- **THEN** the system SHALL return a default value

---

### Requirement: Discovered packages table schema

The discovered_packages table SHALL contain columns: tracking_id (TEXT, PK), vendor (TEXT), source_subject (TEXT), source_sender (TEXT), discovered_at (DATETIME).

#### Scenario: Store discovered package
- **WHEN** a package is discovered from email
- **THEN** it SHALL be stored with tracking_id, vendor, source metadata, and discovery timestamp

---

### Requirement: Schema versioning

The database SHALL include a schema_version table tracking the current schema version. Migration scripts SHALL upgrade the schema from any previous version to the current version.

#### Scenario: Schema migration on upgrade
- **WHEN** the add-on starts with a database at an older schema version
- **THEN** migration scripts SHALL run to bring the schema to the current version

#### Scenario: No migration needed
- **WHEN** the add-on starts with a database already at the current schema version
- **THEN** no migrations SHALL run

---

### Requirement: Async repository layer

The repository layer SHALL provide async CRUD operations for all tables, abstracting SQL details from the service layer.

#### Scenario: Async package retrieval
- **WHEN** the service layer requests all packages
- **THEN** the repository SHALL return them asynchronously without blocking the event loop
