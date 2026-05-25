## ADDED Requirements

### Requirement: Transient error retry

The scraper service SHALL retry fetch operations on transient errors (network timeouts, connection refused, HTTP 5xx) up to 2 times with exponential backoff (5s, 15s). Non-retryable errors (HTTP 4xx, parse errors) SHALL fail immediately.

#### Scenario: Network timeout triggers retry
- **WHEN** a scraper fetch fails with a network timeout
- **THEN** the service SHALL wait 5 seconds and retry the fetch
- **AND** if the retry also fails, SHALL wait 15 seconds and retry once more
- **AND** if all retries fail, SHALL log the error and continue to the next package

#### Scenario: HTTP 500 triggers retry
- **WHEN** a carrier API returns HTTP 500
- **THEN** the service SHALL retry as for network timeouts

#### Scenario: HTTP 404 does not retry
- **WHEN** a carrier API returns HTTP 404 (tracking ID not found)
- **THEN** the service SHALL NOT retry and SHALL immediately log the error

#### Scenario: Auth failure does not retry
- **WHEN** the Posti auth endpoint returns a malformed response
- **THEN** the service SHALL NOT retry and SHALL log the error

---

### Requirement: Scraper error logging

The scraper service SHALL log all scraper failures at WARNING level with the tracking_id, vendor, and error message, providing clear visibility into which packages failed and why.

#### Scenario: Scraper error logged with context
- **WHEN** a scraper fetch fails after all retries
- **THEN** the service SHALL log at WARNING level: "Failed to update {tracking_id} ({vendor}): {error_message}"

#### Scenario: Successful update logged at debug
- **WHEN** a scraper fetch succeeds
- **THEN** the service SHALL log at DEBUG level the status transition
