#!/bin/bash
# Schedule the release bookings on macOS (launchd). Courts are released at 20:00
# eight days ahead, so each job runs at 19:55 the day before, a week early:
#   local.clubspark-bookings.release         Sun-Thu -> Mon-Fri 20:00
#   local.clubspark-bookings.release-sunday  Sat     -> Sun 16:30
#
#   scripts/install-macos.sh            books for real (--confirm)
#   scripts/install-macos.sh --dry-run  stops at the confirmation page each time
#   scripts/install-macos.sh --uninstall
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_DIR="${PLIST_DIR:-$HOME/Library/LaunchAgents}"
DOMAIN="gui/$(id -u)"
CONFIRM="<string>--confirm</string>"
LABELS="local.clubspark-bookings.release local.clubspark-bookings.release-sunday"

case "${1:-}" in
  --uninstall)
    for label in $LABELS; do
      launchctl bootout "$DOMAIN" "$PLIST_DIR/$label.plist" 2>/dev/null || true
      rm -f "$PLIST_DIR/$label.plist"
      echo "Removed $label."
    done
    exit 0 ;;
  --dry-run) CONFIRM="" ;;
  "") ;;
  *) echo "usage: $0 [--dry-run|--uninstall]" >&2; exit 2 ;;
esac

[ -x "$REPO/.venv/bin/clubspark" ] || { echo "Run the README setup first (.venv missing)." >&2; exit 1; }
[ -f "$REPO/.env" ] || { echo "Create $REPO/.env with your ClubSpark login first." >&2; exit 1; }
mkdir -p "$REPO/output/logs" "$PLIST_DIR"

# install_job LABEL "WEEKDAYS (launchd: Sunday=0)" COURT_TIME DESCRIPTION
install_job() {
  local label="$1" weekdays="$2" court_time="$3" description="$4"
  local plist="$PLIST_DIR/$label.plist" calendar="" day
  for day in $weekdays; do
    calendar+="    <dict><key>Weekday</key><integer>$day</integer><key>Hour</key><integer>19</integer><key>Minute</key><integer>55</integer></dict>
"
  done
  cat > "$plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$label</string>
  <key>ProgramArguments</key>
  <array>
    <string>$REPO/.venv/bin/clubspark</string>
    <string>release</string>
    <string>--time</string>
    <string>$court_time</string>
    <string>--headed</string>
    $CONFIRM
  </array>
  <key>WorkingDirectory</key><string>$REPO</string>
  <!-- $description: 19:55, five minutes before the 20:00 release 8 days ahead. -->
  <key>StartCalendarInterval</key>
  <array>
$calendar  </array>
  <key>StandardOutPath</key><string>$REPO/output/logs/release.log</string>
  <key>StandardErrorPath</key><string>$REPO/output/logs/release.log</string>
</dict>
</plist>
PLIST
  if [ "$(uname)" = "Darwin" ]; then
    launchctl bootout "$DOMAIN" "$plist" 2>/dev/null || true
    launchctl bootstrap "$DOMAIN" "$plist"
    echo "Scheduled $label: $description."
  else
    echo "Wrote $plist (not macOS, so not loaded)."
  fi
}

install_job local.clubspark-bookings.release "0 1 2 3 4" 20:00 \
  "Sunday-Thursday 19:55, booking 20:00 Monday-Friday 8 days ahead"
install_job local.clubspark-bookings.release-sunday "6" 16:30 \
  "Saturday 19:55, booking 16:30 Sunday 8 days ahead"

echo "Each checks from 19:58 in a visible browser and books 60 minutes."
echo "Mode: $([ -n "$CONFIRM" ] && echo 'books for real' || echo 'dry run')."
echo "Log: $REPO/output/logs/release.log"
echo "Run one now (REAL booking if before 20:10 on its day): launchctl kickstart $DOMAIN/<label>"
