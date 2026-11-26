# clubspark-bookings

Python + Playwright tools for court bookings at
[Shooters Hill LTC on ClubSpark](https://clubspark.lta.org.uk/ShootersHillLTC/Booking/BookByDate).

## Status (26 Nov 2026)

- Working end to end: the first release run booked Court 5 for Fri 4 Dec at 20:00:06
  (30 min, before 60-minute booking was added).
- Scheduled: Sunday-Thursday at 19:55, booking 20:00-21:00 Monday-Friday 8 days ahead;
  Saturday at 19:55, booking 16:30-17:30 Sunday 8 days ahead.
- Watching: Court 5, Fri 4 Dec 20:30-21:00 for a cancellation
  (`output/logs/watch-court5-2030.log`).

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt -e .
.venv/bin/playwright install chromium   # skip in Claude cloud sessions: Chromium is preinstalled
```

## Usage

```bash
.venv/bin/python -m clubspark_bookings.cli url --date 2026-11-26
.venv/bin/python -m clubspark_bookings.cli availability --date 2026-11-26
```

`availability` saves `output/<date>/page.png` and the JSON the page loads, as a
starting point for parsing free slots.

## Auto-booking 8pm Monday-Friday and 4.30pm Sunday (released 8pm, 8 days before)

Shooters Hill releases each day's courts at 20:00 eight days ahead: Monday's courts
open on the Sunday 8 days before, through to Friday's on the Thursday 8 days before.
So `local.clubspark-bookings.release` runs Sunday-Thursday (20:00 courts), and
`local.clubspark-bookings.release-sunday` runs Saturday (`--time 16:30`, Sunday's
16:30 courts). Each run's `clubspark release`:

1. signs in at 19:55 and loads the page for the day 8 days ahead,
2. from 19:58 refreshes every ~15s, and from 20:00:00 every ~5s, and books
   the hour (20:00-21:00, or 16:30-17:30 on Sundays) on the first court free for
   it, or the longest it can get (moving on to the next court if someone else gets
   one first). Faster refreshing trips Cloudflare's "Verify you are human" check.
3. gives up after 10 minutes and shows a macOS notification with the result.

Set it up on the Mac that stays on (run these from this folder):

```bash
# 1. Install
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt -e .
.venv/bin/playwright install chromium
cp .env.example .env        # fill in CLUBSPARK_USERNAME and CLUBSPARK_PASSWORD

# 2. Sign in by hand once (saves the session; records the sign-in pages for debugging)
.venv/bin/clubspark login

# 3. Rehearse on a date that has a free slot (dry run: stops before confirming)
.venv/bin/clubspark book --date 2026-11-30 --time 18:00 --headed

# 4. Schedule both jobs (Sunday-Thursday and Saturday at 19:55)
scripts/install-macos.sh            # or --dry-run to rehearse a week first
```

Notes:
- Keep this folder **outside** Documents, Desktop and Downloads: macOS blocks
  scheduled jobs from reading those folders unless you grant Full Disk Access.
- The Mac must be awake and you must be logged in at 19:55 every day except Friday. The job opens
  a visible Chromium window; if Cloudflare shows "Verify you are human", tick it
  (the tool never does) and it carries on.
- Notifications also go to your phone by iMessage if `.env` has
  `CLUBSPARK_IMESSAGE_TO=<your phone number or Apple ID email>` (Messages must be signed
  in on the Mac). Check with `.venv/bin/clubspark notify-test`. The first text from the
  scheduled job needs System Settings › Privacy & Security › Automation to allow it to
  control Messages; a failed text is logged and never stops a booking.
- If sign-in or booking fails, a screenshot and a description of the page (visible
  boxes and buttons only, never what was typed) are saved in `output/*/debug/`.
- Log: `output/logs/release.log`; screenshots: `output/booking-<date>/`.
- `launchctl kickstart gui/$(id -u)/<label>` starts a REAL run straight away (before
  20:10 on that job's day it waits for 20:00 and books).
- Remove it: `scripts/install-macos.sh --uninstall`.

## Watch for a cancellation

For a court someone cancels later, run this **on your own computer** (ClubSpark
blocks cloud/data-centre IPs):

```bash
cp .env.example .env   # then fill in CLUBSPARK_USERNAME and CLUBSPARK_PASSWORD
.venv/bin/clubspark book --headed                # dry run: stops at the confirmation page
.venv/bin/clubspark book --confirm               # books for real
```

It signs in (saving the session to `output/booking-<date>/auth.json`), then
checks the next Friday's 20:00 slots every ~60s. When a court is free it books
it, and stops watching 60 minutes before the slot. Options: `--day`, `--date`,
`--time 19:00`, `--interval 90`, `--stop-before 30`. Screenshots of the
confirmation and result are saved next to `auth.json`.

**First run:** the page selectors in `src/clubspark_bookings/selectors.py` are
unverified against the live site. Do a `--headed` dry run first and adjust them
if a step can't find its button.

**Booking length:** 60 minutes by default (`--minutes 30` for half an hour). Courts free
for the whole hour are tried first; if none is, it books the longest a court allows.

Keep the interval at 60s or more so you don't load ClubSpark heavily or get rate-limited.

## Configuration

Environment variables (see `.env.example`): `CLUBSPARK_VENUE`,
`CLUBSPARK_USERNAME`, `CLUBSPARK_PASSWORD`. Credentials are only read from the
environment; never commit them.

## Tests

```bash
.venv/bin/python -m pytest
```
