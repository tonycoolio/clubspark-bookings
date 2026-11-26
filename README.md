# clubspark-bookings

Python + Playwright tools for court bookings at
[Shooters Hill LTC on ClubSpark](https://clubspark.lta.org.uk/ShootersHillLTC/Booking/BookByDate).

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

## Weekly auto-booking (Friday 8pm, released Thursday 8pm)

Shooters Hill releases each day's courts at 20:00 eight days ahead, so Friday
courts open at 20:00 on the Thursday of the week before. `clubspark release`:

1. signs in a few minutes early and loads the target Friday's page,
2. from 20:00:00 refreshes every ~2s and books the first free 20:00 court
   (moving on to the next court if someone else gets one first),
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

# 4. Schedule it every Thursday at 19:55
scripts/install-macos.sh            # or --dry-run to rehearse a week first
```

Notes:
- Keep this folder **outside** Documents, Desktop and Downloads: macOS blocks
  scheduled jobs from reading those folders unless you grant Full Disk Access.
- The Mac must be awake and you must be logged in at 19:55 on Thursday.
- If sign-in or booking fails, a screenshot and a description of the page (visible
  boxes and buttons only, never what was typed) are saved in `output/*/debug/`.
- Log: `output/logs/release.log`; screenshots: `output/booking-<date>/`.
- Test the scheduled job right away: `launchctl kickstart gui/$(id -u)/local.clubspark-bookings.release`.
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
if a step can't find its button. Booking uses the venue's default duration;
check the confirmation screenshot shows the length and price you expect.

Keep the interval at 60s or more so you don't load ClubSpark heavily or get rate-limited.

## Configuration

Environment variables (see `.env.example`): `CLUBSPARK_VENUE`,
`CLUBSPARK_USERNAME`, `CLUBSPARK_PASSWORD`. Credentials are only read from the
environment; never commit them.

## Tests

```bash
.venv/bin/python -m pytest
```
