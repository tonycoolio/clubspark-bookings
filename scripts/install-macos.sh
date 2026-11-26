#!/bin/bash
# Schedule the release bookings on macOS (launchd): Sun-Thu 19:55 for Mon-Fri courts 8 days ahead.
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

CALENDAR=""
for day in 0 1 2 3 4; do
  CALENDAR+="    <dict><key>Weekday</key><integer>$day</integer><key>Hour</key><integer>19</integer><key>Minute</key><integer>55</integer></dict>
"
done

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
    <string>--headed</string>
    $CONFIRM
  </array>
  <key>WorkingDirectory</key><string>$REPO</string>
  <!-- Sunday-Thursday (launchd: Sunday=0) at 19:55, five minutes before the 20:00
       release of the courts 8 days ahead: Monday-Friday of the week after next. -->
  <key>StartCalendarInterval</key>
  <array>
$CALENDAR  </array>
  <key>StandardOutPath</key><string>$REPO/output/logs/release.log</string>
  <key>StandardErrorPath</key><string>$REPO/output/logs/release.log</string>
</dict>
</plist>
PLIST

if [ "$(uname)" = "Darwin" ]; then
  launchctl bootout "$DOMAIN" "$PLIST" 2>/dev/null || true
  launchctl bootstrap "$DOMAIN" "$PLIST"
  echo "Scheduled: Sunday-Thursday 19:55, booking 20:00 Monday-Friday 8 days ahead (checks from 19:58, visible browser)"
  echo "Mode: $([ -n "$CONFIRM" ] && echo 'books for real' || echo 'dry run')."
  echo "Log: $REPO/output/logs/release.log"
  echo "Test now: launchctl kickstart $DOMAIN/$LABEL"
else
  echo "Wrote $PLIST (not macOS, so not loaded)."
fi
