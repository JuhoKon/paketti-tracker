## ADDED Requirements

### Requirement: HACS repository metadata

The repository SHALL include a `hacs.json` file at the root with valid metadata so HACS can discover and install the integration.

#### Scenario: HACS recognizes the repository
- **WHEN** a user adds this repository as a custom HACS repository
- **THEN** HACS SHALL parse `hacs.json` and display the integration name and version without errors

### Requirement: Version tag matches manifest

The repository SHALL have a git tag matching the `version` field in `manifest.json` using plain semver format (e.g. `0.9.0`).

#### Scenario: HACS resolves version from tag
- **WHEN** HACS checks for available versions
- **THEN** it SHALL find a tag whose value matches `manifest.json` version and offer it for installation

#### Scenario: No version mismatch error
- **WHEN** a user installs the integration via HACS
- **THEN** HACS SHALL NOT display "The version X for this integration can not be used with HACS"
