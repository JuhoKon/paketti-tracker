## Why

HACS rejects the integration with error: "The version 2a4b025 for this integration can not be used with HACS." This happens because HACS determines the integration version from git tags, and without a proper semver tag it falls back to the commit SHA — which is not a valid version string.

## What Changes

- Add `hacs.json` at repository root with required HACS metadata (render_readme, content_in_root path)
- Ensure `manifest.json` version field is aligned with git tag versioning
- Create a semver git tag (e.g. `v0.1.0`) matching `manifest.json` version

## Non-goals

- No functional changes to the integration itself
- No new HA entity platforms

## Capabilities

### New Capabilities

### Modified Capabilities

## Impact

- Repository root: new `hacs.json` file
- Git: new version tag required for HACS compatibility
- No code changes to the integration logic
