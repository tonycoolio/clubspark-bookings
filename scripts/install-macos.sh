#!/bin/bash
# Schedule the weekly release booking on macOS (launchd).
#   scripts/install-macos.sh            books for real (--confirm)
#   scripts/install-macos.sh --dry-run  stops at the confirmation page each week
#   scripts/install-macos.sh --uninstall
set -euo pipefail

LABEL="local.clubspark-bookings.release"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PLIST="${PLIST_DIR:-$HOME/Library/LaunchAgents}/$LABEL.plist"
DOMAIN="gui/$(id -u)"
CONFIRM="<string>--confirm</string>"

case "${1:-}" in
  --uninstall)
    launchctl bootout "$DOMAIN" "$PLIST" 2>/dev/null || true
    rm -f "$PLIST"
    echo "Removed $LABEL."
    exit 0 ;;
  --dry-run) CONFIRM="" ;;
  "") ;;
  *) echo "usage: $0 [--dry-run|--uninstall]" >&2; exit 2 ;;
esac

[ -x "$REPO/.venv/bin/clubspark" ] || { echo "Run the README setup first (.venv missing)." >&2; exit 1; }
[ -f "$REPO/.env" ] || { echo "Create $REPO/.env with your ClubSpark login first." >&2; exit 1; }
mkdir -p "$REPO/output/logs" "$(dirname "$PLIST")"

cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$REPO/.venv/bin/clubspark</string>
    <string>release</string>
    $CONFIRM
  </array>
  <key>WorkingDirectory</key><string>$REPO</string>
  <!-- Every Thursday (launchd: Sunday=0) at 19:55, five minutes before release. -->
  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key><integer>4</integer>
    <key>Hour</key><integer>19</integer>
    <key>Minute</key><integer>55</integer>
  </dict>
  <key>StandardOutPath</key><string>$REPO/output/logs/release.log</string>
  <key>StandardErrorPath</key><string>$REPO/output/logs/release.log</string>
</dict>
</plist>
PLIST

if [ "$(uname)" = "Darwin" ]; then
  launchctl bootout "$DOMAIN" "$PLIST" 2>/dev/null || true
  launchctl bootstrap "$DOMAIN" "$PLIST"
  echo "Scheduled: every Thursday 19:55 ($([ -n "$CONFIRM" ] && echo 'books for real' || echo 'dry run'))."
  echo "Log: $REPO/output/logs/release.log"
  echo "Test now: launchctl kickstart $DOMAIN/$LABEL"
else
  echo "Wrote $PLIST (not macOS, so not loaded)."
fi
