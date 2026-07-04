#!/usr/bin/env bash
# Create a GitHub release from docs/releases/RELEASE_NOTES_vX.Y.Z.md
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

usage() {
  cat <<'EOF'
Usage: create_release.sh <version> [title]

  version   e.g. 3.11.8 or v3.11.8
  title     optional; default parsed from release notes (first heading)

Examples:
  ./scripts/release/create_release.sh 3.11.8
  ./scripts/release/create_release.sh v3.11.8 "v3.11.8 — Custom title"
EOF
}

if [[ $# -lt 1 || "$1" == "-h" || "$1" == "--help" ]]; then
  usage
  exit 0
fi

RAW_VERSION="$1"
VERSION="${RAW_VERSION#v}"
TAG="v${VERSION}"
NOTES_FILE="docs/releases/RELEASE_NOTES_v${VERSION}.md"

if [[ ! -f "$NOTES_FILE" ]]; then
  echo "Release notes not found: $NOTES_FILE" >&2
  exit 1
fi

if [[ $# -ge 2 ]]; then
  TITLE="$2"
else
  FIRST_LINE="$(grep -m1 '^#' "$NOTES_FILE" || true)"
  SUBTITLE="$(echo "$FIRST_LINE" | sed -E 's/^# v[0-9.]+ \([^)]+\) — //; s/^# v[0-9.]+ - //; s/^# v[0-9.]+ — //')"
  if [[ -n "$SUBTITLE" && "$SUBTITLE" != "$FIRST_LINE" ]]; then
    TITLE="${TAG} — ${SUBTITLE}"
  else
    TITLE="$TAG"
  fi
fi

# Avoid proxy issues in some IDE terminals (same as legacy release_push scripts)
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy 2>/dev/null || true

echo "Creating GitHub release ${TAG}..."
echo "  Title: ${TITLE}"
echo "  Notes: ${NOTES_FILE}"

if gh release create "$TAG" --title "$TITLE" --notes-file "$NOTES_FILE"; then
  echo "Done: https://github.com/tinel-c/ServerBootShutdownManagemement/releases/tag/${TAG}"
else
  echo >&2
  echo "If gh failed, create the release in the browser:" >&2
  echo "  https://github.com/tinel-c/ServerBootShutdownManagemement/releases/new?tag=${TAG}" >&2
  echo "  Title: ${TITLE}" >&2
  echo "  Paste content from ${NOTES_FILE}" >&2
  exit 1
fi
