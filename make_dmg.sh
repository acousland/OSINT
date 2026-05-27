#!/bin/bash
#
# Build a standard macOS .dmg installer: a window where the user drags OSIntel.app onto
# an Applications shortcut. Produces dist/OSIntel-Installer.dmg.
#
# Requires: create-dmg (brew install create-dmg), and a built /Applications/OSIntel.app
# (run ./install.sh first, or this script will build it).
#
set -euo pipefail
cd "$(dirname "$0")"

APP="/Applications/OSIntel.app"
DMG="dist/OSIntel-Installer.dmg"
VOLNAME="OSIntel"
STAGE="dist/dmg-src"

if ! command -v create-dmg >/dev/null 2>&1; then
  echo "error: create-dmg not found. Install with: brew install create-dmg" >&2
  exit 1
fi

if [[ ! -d "$APP" ]]; then
  echo "==> $APP not found; building it"
  ./install.sh >/dev/null
fi

echo "==> Generating installer background"
swift tools/make_dmg_background.swift

echo "==> Staging app"
rm -rf "$STAGE"; mkdir -p "$STAGE"
# Copy with -c to preserve the code signature.
cp -Rc "$APP" "$STAGE/"

echo "==> Building $DMG"
rm -f "$DMG"
create-dmg \
  --volname "$VOLNAME" \
  --background "dist/dmg-background.png" \
  --window-pos 200 120 \
  --window-size 660 400 \
  --icon-size 120 \
  --icon "OSIntel.app" 165 200 \
  --app-drop-link 495 200 \
  --hide-extension "OSIntel.app" \
  --no-internet-enable \
  "$DMG" \
  "$STAGE"

rm -rf "$STAGE"
echo "==> Done: $DMG"
