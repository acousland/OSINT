#!/bin/bash
#
# Build OSIntel in Release configuration and install it to /Applications.
#
# Usage:
#   ./install.sh              # build + install to /Applications
#   ./install.sh --debug      # build the Debug configuration instead of Release
#   DEST=~/Applications ./install.sh   # install somewhere other than /Applications
#
set -euo pipefail

cd "$(dirname "$0")"

CONFIG="Release"
[[ "${1:-}" == "--debug" ]] && CONFIG="Debug"
DEST="${DEST:-/Applications}"
APP_NAME="OSIntel.app"
DERIVED=".build"

echo "==> Stamping BuildInfo with current git commit"
GEN="Sources/Generated/BuildInfo.swift"
mkdir -p "$(dirname "$GEN")"
HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
git diff --quiet 2>/dev/null || HASH="$HASH-dirty"
VER=$(grep 'MARKETING_VERSION' project.yml | head -1 | sed 's/.*"\(.*\)".*/\1/')
cat > "$GEN" <<EOF
// Generated at build time by install.sh — do not edit.
enum BuildInfo {
    static let version = "${VER:-1.1.0}"
    static let commit = "$HASH"
    static let date = "$(date +%Y-%m-%d)"
}
EOF
echo "    version ${VER:-1.1.0}, commit $HASH"

echo "==> Regenerating Xcode project (xcodegen)"
if ! command -v xcodegen >/dev/null 2>&1; then
  echo "error: xcodegen not found. Install it with: brew install xcodegen" >&2
  exit 1
fi
xcodegen generate >/dev/null

echo "==> Building OSIntel ($CONFIG)"
xcodebuild \
  -project OSIntel.xcodeproj \
  -scheme OSIntel \
  -configuration "$CONFIG" \
  -destination 'platform=macOS' \
  -derivedDataPath "$DERIVED" \
  build >/dev/null

SRC="$DERIVED/Build/Products/$CONFIG/$APP_NAME"
if [[ ! -d "$SRC" ]]; then
  echo "error: build product not found at $SRC" >&2
  exit 1
fi

echo "==> Installing to $DEST/$APP_NAME"
if [[ ! -w "$DEST" ]]; then
  echo "error: $DEST is not writable. Re-run with: DEST=~/Applications ./install.sh" >&2
  exit 1
fi
rm -rf "${DEST:?}/$APP_NAME"
# -c preserves code-signature/extended attributes during the copy.
cp -Rc "$SRC" "$DEST/"

echo "==> Done. Installed $DEST/$APP_NAME"
echo "    Launch with: open \"$DEST/$APP_NAME\""
