## ADDED Requirements

### Requirement: Package list endpoint

The API SHALL provide GET /api/packages returning all tracked packages as a JSON array.

#### Scenario: List packages
- **WHEN** a GET request is made to /api/packages
- **THEN** the response SHALL be HTTP 200 with a JSON array of package objects

---

### Requirement: Add package endpoint

The API SHALL provide POST /api/packages accepting tracking_id, vendor, and name to create a new tracked package.

#### Scenario: Add valid package
- **WHEN** a POST request is made to /api/packages with valid tracking_id, vendor, and name
- **THEN** the response SHALL be HTTP 201 with the created package object

#### Scenario: Add package with missing fields
- **WHEN** a POST request is made with missing required fields
- **THEN** the response SHALL be HTTP 422 with validation error detail

---

### Requirement: Edit package endpoint

The API SHALL provide PATCH /api/packages/{tracking_id} to update name or vendor of an existing package.

#### Scenario: Edit existing package
- **WHEN** a PATCH request is made to /api/packages/{tracking_id} with a new name
- **THEN** the response SHALL be HTTP 200 with the updated package object

#### Scenario: Edit non-existent package
- **WHEN** a PATCH request is made for a tracking_id that does not exist
- **THEN** the response SHALL be HTTP 404

---

### Requirement: Delete package endpoint

The API SHALL provide DELETE /api/packages/{tracking_id} to remove a tracked package.

#### Scenario: Delete existing package
- **WHEN** a DELETE request is made to /api/packages/{tracking_id}
- **THEN** the response SHALL be HTTP 204 and the package SHALL be removed

#### Scenario: Delete non-existent package
- **WHEN** a DELETE request is made for a tracking_id that does not exist
- **THEN** the response SHALL be HTTP 404

---

### Requirement: Refresh endpoint

The API SHALL provide POST /api/packages/refresh to trigger an immediate poll of all active packages.

#### Scenario: Trigger refresh
- **WHEN** a POST request is made to /api/packages/refresh
- **THEN** the response SHALL be HTTP 202 and a background poll SHALL be initiated

---

### Requirement: Settings endpoints

The API SHALL provide GET /api/settings and PATCH /api/settings for reading and updating general settings (poll interval).

#### Scenario: Get settings
- **WHEN** a GET request is made to /api/settings
- **THEN** the response SHALL be HTTP 200 with current settings including poll_interval

#### Scenario: Update poll interval
- **WHEN** a PATCH request is made to /api/settings with a new poll_interval value
- **THEN** the response SHALL be HTTP 200 and the poll interval SHALL be updated

---

### Requirement: Notification config endpoints

The API SHALL provide GET /api/notifications and PATCH /api/notifications for notification configuration.

#### Scenario: Get notification config
- **WHEN** a GET request is made to /api/notifications
- **THEN** the response SHALL be HTTP 200 with triggers, devices, and enabled status

#### Scenario: Update notification config
- **WHEN** a PATCH request is made to /api/notifications with updated triggers
- **THEN** the response SHALL be HTTP 200 with the updated configuration

---

### Requirement: Email config endpoints

The API SHALL provide GET /api/email (password masked), PATCH /api/email, POST /api/email/test, GET /api/email/discovered, POST /api/email/discovered/{tracking_id}/confirm, and DELETE /api/email/discovered/{tracking_id}.

#### Scenario: Get email config with masked password
- **WHEN** a GET request is made to /api/email
- **THEN** the response SHALL be HTTP 200 with IMAP config where the password field is masked

#### Scenario: Test IMAP connection
- **WHEN** a POST request is made to /api/email/test
- **THEN** the response SHALL indicate success or failure of the IMAP connection attempt

#### Scenario: Confirm discovered package
- **WHEN** a POST request is made to /api/email/discovered/{tracking_id}/confirm
- **THEN** the package SHALL be added to tracked packages and removed from discovered list

#### Scenario: Dismiss discovered package
- **WHEN** a DELETE request is made to /api/email/discovered/{tracking_id}
- **THEN** the discovered package SHALL be removed without adding to tracked packages

---

### Requirement: Consistent error responses

All endpoints SHALL return JSON with appropriate HTTP status codes. Validation errors SHALL return HTTP 422 with a detail field describing the error.

#### Scenario: Invalid JSON body
- **WHEN** a request is made with an invalid JSON body
- **THEN** the response SHALL be HTTP 422 with detail explaining the validation failure
