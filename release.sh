#!/bin/bash
#
# Build OSIntel (Release), package it, and publish to GitHub as the rolling "latest"
# release so it can be downloaded from the Releases section. Re-runnable: each run
# rebuilds, moves the `latest` tag to the current commit, and replaces the asset.
#
# Constant download URL:
#   https://github.com/acousland/OSINT/releases/latest/download/OSIntel-macos.zip
#
# Requires: gh (authenticated), xcodegen, Xcode. Usage:  ./release.sh
#
set -euo pipefail
cd "$(dirname "$0")"

TAG="latest"
TITLE="OSIntel (latest)"
ASSET="dist/OSIntel-macos.zip"
APP="/Applications/OSIntel.app"

echo "==> Building + installing current Release"
./install.sh >/dev/null

echo "==> Packaging $ASSET"
mkdir -p dist
rm -f "$ASSET"
# ditto preserves the code signature and bundle structure inside the zip.
ditto -c -k --keepParent "$APP" "$ASSET"

echo "==> Moving rolling '$TAG' tag to current commit and pushing"
git tag -f "$TAG"
git push -f origin "$TAG"

NOTES=$(cat <<'EOF'
Latest build of the OSIntel native macOS app.

**Install**
1. Download `OSIntel-macos.zip` below and unzip.
2. Move `OSIntel.app` to `/Applications`.
3. This build is **ad-hoc signed (not notarized)**, so macOS Gatekeeper will quarantine it.
   Clear the flag once:
   ```
   xattr -dr com.apple.quarantine /Applications/OSIntel.app
   ```
   …or right-click the app → **Open** the first time.
4. In the app, open **Settings (⌘,)** and add your ABR GUID and OpenAI API key.
EOF
)

if gh release view "$TAG" >/dev/null 2>&1; then
  echo "==> Updating existing '$TAG' release"
  gh release upload "$TAG" "$ASSET" --clobber
  gh release edit "$TAG" --latest --title "$TITLE" --notes "$NOTES"
else
  echo "==> Creating '$TAG' release"
  gh release create "$TAG" "$ASSET" --latest --title "$TITLE" --notes "$NOTES"
fi

echo "==> Done. https://github.com/acousland/OSINT/releases/latest"
