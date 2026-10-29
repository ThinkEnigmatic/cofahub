#!/bin/bash
# Build the SwiftUI shell and assemble a minimal, ad-hoc-signed .app bundle.
# Not sandboxed: the app must launch a local Python server and read ~/cofa-forward.
set -euo pipefail
cd "$(dirname "$0")"

swift build -c release

BIN=".build/release/COFAForward"
APP="COFAHUB.app"

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS"
cp "$BIN" "$APP/Contents/MacOS/COFAForward"

cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>COFAHUB</string>
  <key>CFBundleDisplayName</key><string>COFAHUB</string>
  <key>CFBundleIdentifier</key><string>com.thinkenigmatic.cofaforward</string>
  <key>CFBundleExecutable</key><string>COFAForward</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleVersion</key><string>0.1.0</string>
  <key>CFBundleShortVersionString</key><string>0.1.0</string>
  <key>LSMinimumSystemVersion</key><string>14.0</string>
  <key>NSHighResolutionCapable</key><true/>
  <key>NSAppTransportSecurity</key>
  <dict>
    <key>NSAllowsLocalNetworking</key><true/>
  </dict>
</dict>
</plist>
PLIST

codesign --force --deep --sign - "$APP"
echo "Built $APP"
