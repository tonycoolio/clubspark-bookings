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

## Auto-book Friday 8pm

Run this **on your own computer** (ClubSpark blocks cloud/data-centre IPs):

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
