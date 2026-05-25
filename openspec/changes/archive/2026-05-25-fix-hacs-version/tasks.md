## 1. HACS Metadata

- [x] 1.1 Create `hacs.json` at repository root with fields: `name`, `content_in_root: false`, `homeassistant` minimum version
- [x] 1.2 Verify `manifest.json` has a valid `version` field (semver format, no leading `v`)

## 2. Git Tag & Release

- [x] 2.1 Commit all changes (including `hacs.json`)
- [x] 2.2 Create git tag `0.9.0` matching `manifest.json` version
- [x] 2.3 Push tag to remote
- [x] 2.4 Create a GitHub Release from the tag (required — HACS needs a release, not just a tag)

## 3. Verification

- [x] 3.1 Confirm HACS can resolve the version without error (no "can not be used with HACS" message)
