## 1. Add-on Options Schema

- [x] 1.1 Add email fields to `addon/config.yaml` options (email_enabled, email_host, email_port, email_username, email_password, email_folder, email_auto_add) with defaults
- [x] 1.2 Add email fields to `addon/config.yaml` schema (bool, str, int, str, password, str, bool)
- [x] 1.3 Export email env vars from bashio::config in `addon/run.sh` (with null filtering)

## 2. Settings Dataclass

- [x] 2.1 Add email fields to `addon/app/config.py` Settings dataclass (email_enabled, email_host, email_port, email_username, email_password, email_folder, email_auto_add)
- [x] 2.2 Read from env vars with same defaults as config.yaml

## 3. Email Service Integration

- [x] 3.1 Update `EmailService.__init__` to accept Settings instead of reading from DB
- [x] 3.2 Skip IMAP connection when email_enabled is false or host is empty
- [x] 3.3 Update `EmailClient` instantiation to use Settings fields
- [x] 3.4 Remove DB-based email config read in email service poll loop

## 4. REST API Changes

- [x] 4.1 Update `GET /api/email` to return config from Settings (env vars) instead of DB
- [x] 4.2 Remove or replace `PUT /api/email` endpoint (return 405)
- [x] 4.3 Keep discovered packages endpoints unchanged

## 5. Frontend Update

- [x] 5.1 Update SettingsPage email section to display config as read-only
- [x] 5.2 Add "Configure in Add-on Options" message with visual indicator
- [x] 5.3 Remove email config form/save button from frontend
- [x] 5.4 Update API client to remove email config write calls

## 6. Testing

- [x] 6.1 Update email service tests to use Settings instead of DB config
- [x] 6.2 Test email service skips when disabled
- [x] 6.3 Verify existing test suite passes (`python -m pytest tests/addon/ -v`)
- [x] 6.4 Docker build and startup test with email options set
