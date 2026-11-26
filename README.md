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

## Configuration

Environment variables (see `.env.example`): `CLUBSPARK_VENUE`,
`CLUBSPARK_USERNAME`, `CLUBSPARK_PASSWORD`. Credentials are only read from the
environment; never commit them.

## Tests

```bash
.venv/bin/python -m pytest
```
