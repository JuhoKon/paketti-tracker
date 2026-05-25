## MODIFIED Requirements

### Requirement: Common scraper interface

All carrier scrapers SHALL implement a common interface (abstract base class or Protocol) that accepts a tracking ID and a standalone aiohttp.ClientSession, and returns a `TrackingResult` or raises a `ScraperError`.

#### Scenario: Scraper returns result on success
- **WHEN** a scraper is called with a valid tracking ID and the carrier endpoint responds successfully
- **THEN** the scraper SHALL return a `TrackingResult` with at minimum a normalized status and a non-empty events list

#### Scenario: Scraper raises ScraperError on failure
- **WHEN** a carrier endpoint returns an error response or the response cannot be parsed
- **THEN** the scraper SHALL raise `ScraperError` with a descriptive message

#### Scenario: Scraper raises ScraperError on network timeout
- **WHEN** the carrier endpoint does not respond within the timeout
- **THEN** the scraper SHALL raise `ScraperError`

#### Scenario: Session is standalone (not HA-provided)
- **WHEN** the scraper is initialized
- **THEN** it SHALL use a standalone aiohttp.ClientSession managed by the application, not hass.async_get_clientsession()
