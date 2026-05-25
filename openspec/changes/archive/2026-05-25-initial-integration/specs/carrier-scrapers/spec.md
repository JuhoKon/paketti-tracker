## ADDED Requirements

### Requirement: Common scraper interface
All carrier scrapers SHALL implement a common interface (abstract base class or Protocol) that accepts a tracking ID and the HA aiohttp client session, and returns a `TrackingResult` or raises a `ScraperError`.

#### Scenario: Scraper returns result on success
- **WHEN** a scraper is called with a valid tracking ID and the carrier endpoint responds successfully
- **THEN** the scraper SHALL return a `TrackingResult` with at minimum a normalized status and a non-empty events list

#### Scenario: Scraper raises ScraperError on failure
- **WHEN** a carrier endpoint returns an error response or the response cannot be parsed
- **THEN** the scraper SHALL raise `ScraperError` with a descriptive message

#### Scenario: Scraper raises ScraperError on network timeout
- **WHEN** the carrier endpoint does not respond within the timeout
- **THEN** the scraper SHALL raise `ScraperError`

---

### Requirement: TrackingResult data model
The `TrackingResult` dataclass SHALL contain: `tracking_id` (str), `vendor` (str), `status` (normalized str), `estimated_delivery` (date or None), `last_location` (str or None), `last_event_time` (datetime or None), `events` (list of `TrackingEvent`), `delivered` (bool).

The `TrackingEvent` dataclass SHALL contain: `timestamp` (datetime), `location` (str or None), `description` (str).

#### Scenario: TrackingResult fully populated
- **WHEN** a carrier provides all fields
- **THEN** `TrackingResult` SHALL have all fields populated with typed values

#### Scenario: TrackingResult with missing optional fields
- **WHEN** a carrier omits estimated delivery or location
- **THEN** the corresponding fields SHALL be `None` and no exception SHALL be raised

---

### Requirement: Posti scraper
The integration SHALL include a scraper for Posti that retrieves tracking data from Posti's internal tracking endpoint and maps Finnish-language status strings to the normalized vocabulary.

#### Scenario: Posti tracking data retrieved
- **WHEN** the Posti scraper is called with a valid Posti tracking ID
- **THEN** it SHALL return a `TrackingResult` with status, events, and available optional fields populated

#### Scenario: Posti status string normalized
- **WHEN** the Posti endpoint returns a Finnish-language status
- **THEN** the scraper SHALL map it to the correct normalized status value

---

### Requirement: Postnord scraper
The integration SHALL include a scraper for Postnord that retrieves tracking data from Postnord's internal tracking endpoint.

#### Scenario: Postnord tracking data retrieved
- **WHEN** the Postnord scraper is called with a valid Postnord tracking ID
- **THEN** it SHALL return a `TrackingResult` with status, events, and available optional fields populated

#### Scenario: Postnord response language
- **WHEN** the Postnord scraper makes a request
- **THEN** it SHALL request English or Finnish language content via appropriate request headers or query parameters

---

### Requirement: Matkahuolto scraper
The integration SHALL include a scraper for Matkahuolto that retrieves tracking data from Matkahuolto's tracking endpoint (JSON API or HTML fallback).

#### Scenario: Matkahuolto tracking data retrieved
- **WHEN** the Matkahuolto scraper is called with a valid Matkahuolto tracking ID
- **THEN** it SHALL return a `TrackingResult` with status, events, and available optional fields populated

---

### Requirement: Scraper factory
A factory function SHALL return the correct scraper instance given a vendor identifier string.

#### Scenario: Known vendor returns scraper
- **WHEN** the factory is called with a known vendor identifier (`posti`, `postnord`, `matkahuolto`)
- **THEN** it SHALL return the corresponding scraper instance

#### Scenario: Unknown vendor raises error
- **WHEN** the factory is called with an unrecognized vendor string
- **THEN** it SHALL raise a `ValueError`
