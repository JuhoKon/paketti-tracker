## Context

HACS (Home Assistant Community Store) determines an integration's version from git tags. When no valid semver tag exists, it uses the commit SHA as the version string. The SHA `2a4b025` is not valid semver, so HACS rejects it.

Current state:
- `manifest.json` has `"version": "0.7.0"` but no corresponding git tag exists
- No `hacs.json` metadata file exists at the repository root
- HACS requires either a tag-based version or explicit configuration

## Goals / Non-Goals

**Goals:**
- Make the integration installable via HACS without version errors
- Establish a repeatable versioning workflow for future releases

**Non-Goals:**
- Changing integration functionality
- Setting up CI/CD or automated releases
- Publishing to the HACS default repository list

## Decisions

### 1. Add `hacs.json` with `content_in_root: false`

HACS needs a `hacs.json` at the repo root to understand the repository layout. Key fields:
- `name`: Display name in HACS
- `content_in_root`: `false` (our code lives in `custom_components/paketti_tracker/`, not at root)
- `homeassistant`: minimum HA version (align with what we actually require)

**Alternative considered:** Relying solely on `manifest.json` — rejected because HACS uses `hacs.json` for repository-level metadata that `manifest.json` doesn't cover.

### 2. Tag releases with semver matching `manifest.json`

HACS reads the version from git tags. The tag format should be plain semver without `v` prefix (e.g. `0.7.0`) to match `manifest.json` directly.

**Alternative considered:** Using `v`-prefixed tags (e.g. `v0.7.0`) — this also works but requires HACS to strip the prefix. Plain semver is simpler and avoids mismatch.

### 3. Keep `version` in `manifest.json` as source of truth

The workflow is: bump version in `manifest.json`, commit, tag, push. HACS reads the tag to find which release to offer.

## Risks / Trade-offs

- [Risk] Forgetting to tag after version bump → HACS shows stale version. Mitigation: document the release process in README.
- [Risk] Tag/manifest version mismatch → HACS confusion. Mitigation: single simple workflow, future CI can validate.
