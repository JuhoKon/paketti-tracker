#!/usr/bin/env bash
set -euo pipefail

# Release script for Paketti Tracker
# Usage: ./release.sh <version>
# Example: ./release.sh 0.2.0

VERSION="${1:-}"

if [ -z "$VERSION" ]; then
  echo "Usage: ./release.sh <version>"
  echo "Example: ./release.sh 0.2.0"
  exit 1
fi

# Validate semver format
if ! echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "Error: Version must be in semver format (e.g. 0.2.0)"
  exit 1
fi

MANIFEST="custom_components/paketti_tracker/manifest.json"

# Check we're in the repo root
if [ ! -f "$MANIFEST" ]; then
  echo "Error: Must be run from the repository root"
  exit 1
fi

# Check for clean working tree
if [ -n "$(git status --porcelain)" ]; then
  echo "Error: Working tree is not clean. Commit or stash changes first."
  exit 1
fi

# Check tag doesn't already exist
if git rev-parse "$VERSION" >/dev/null 2>&1; then
  echo "Error: Tag $VERSION already exists"
  exit 1
fi

echo "Releasing version $VERSION..."

# Update version in manifest.json
sed -i '' "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" "$MANIFEST"

# Commit, tag, push
git add "$MANIFEST"
git commit -m "chore: bump version to $VERSION"
git tag "$VERSION"
git push origin main
git push origin "$VERSION"

# Create GitHub Release
gh release create "$VERSION" --title "v$VERSION" --generate-notes

echo ""
echo "Released v$VERSION successfully!"
echo "  - manifest.json updated"
echo "  - Tag pushed: $VERSION"
echo "  - GitHub Release created"
