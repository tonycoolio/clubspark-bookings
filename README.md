# clubspark-bookings

Python + Playwright tools for court bookings at
[Shooters Hill LTC on ClubSpark](https://clubspark.lta.org.uk/ShootersHillLTC/Booking/BookByDate).

## Tonight's plan: first release, Thu 26 Nov 2026 (courts for Fri 4 Dec)

| When (Thu 26 Nov) | What |
| --- | --- |
| 13:00 | Unattended dry-run rehearsal (Claude scheduled task `clubspark-rehearsal`). Checks the booking pop-up's continue and confirm buttons, fixes their selectors if needed and pushes; never books. A Mac notification gives the result. |
| 19:53 / 19:58 | Calendar reminder: be ready to book by hand. |
| 19:55 | launchd job `local.clubspark-bookings.release` signs in (visible Chromium window). |
| 19:58 | Starts checking Fri 4 Dec every ~15s, then every ~5s from 20:00; books the first free 20:00 court for real. |
| 20:10 | Gives up if nothing was booked; Mac notification with the result. |

Status and risks:
- Confirmed on the live site: automatic sign-in, the booking grid, and free (`FREE`) vs taken slots.
- Not yet confirmed: the pop-up's continue button and the confirm button (the 13:00 rehearsal checks them).
- Cloudflare's "Verify you are human" check blocked the automated browser early on 26 Nov,
  after many quick page loads while testing. If it appears tonight, tick it in the
  Chromium window (the tool never does). If it won't clear, **book by hand at 20:00**:
  [Fri 4 Dec grid](https://clubspark.lta.org.uk/ShootersHillLTC/Booking/BookByDate#?date=2026-12-04&role=member).
- If you get a "Court booked" notification or a confirmation email, there's no need to book by hand.
- Mac must stay on, awake and logged in, with the Claude app open for the 13:00 rehearsal.
- Afterwards: check `output/logs/release.log` and `output/booking-2026-12-04/`.

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

1. signs in at 19:55 and loads the target Friday's page,
2. from 19:58 refreshes every ~15s, and from 20:00:00 every ~5s, and books
   20:00-21:00 on the first court free for the hour (or the longest it can get) (moving on to the next court if someone else gets one
   first). Faster refreshing trips Cloudflare's "Verify you are human" check.
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
- The Mac must be awake and you must be logged in at 19:55 on Thursday. The job opens
  a visible Chromium window; if Cloudflare shows "Verify you are human", tick it
  (the tool never does) and it carries on.
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
