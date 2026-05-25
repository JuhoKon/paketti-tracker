## MODIFIED Requirements

### Requirement: Add-on manifest configuration

The add-on SHALL provide a config.yaml defining metadata including name, version, supported architectures, ingress configuration, exposed ports, configurable options (including email IMAP settings), and `init: false`.

#### Scenario: Supervisor reads config.yaml with email options
- **WHEN** the add-on is installed or options are changed
- **THEN** Supervisor SHALL parse config.yaml with email options: email_enabled (bool), email_host (str), email_port (int), email_username (str), email_password (password), email_folder (str), email_auto_add (bool)

#### Scenario: Email options have sensible defaults
- **WHEN** the add-on is installed without user customization
- **THEN** email_enabled SHALL default to false
- **AND** email_host SHALL default to empty string
- **AND** email_port SHALL default to 993
- **AND** email_username SHALL default to empty string
- **AND** email_password SHALL default to empty string
- **AND** email_folder SHALL default to "INBOX"
- **AND** email_auto_add SHALL default to false

#### Scenario: Password masked in HA UI
- **WHEN** the user views add-on options in HA
- **THEN** the email_password field SHALL be displayed as a password (masked) input
