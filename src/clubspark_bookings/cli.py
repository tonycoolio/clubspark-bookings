"""Command line entry point (installed as `clubspark`)."""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

from .booker import BlockedError, watch_and_book
from .browser import capture_availability
from .config import Config, booking_url
from .slots import next_weekday, to_minutes

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def load_dotenv(path: Path = Path(".env")) -> None:
    """Minimal .env loader so credentials can live in a git-ignored file."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="clubspark")
    sub = parser.add_subparsers(dest="command", required=True)

    avail = sub.add_parser("availability", help="Capture the guest booking page for a date")
    avail.add_argument("--date", type=date.fromisoformat, default=date.today())
    avail.add_argument("--out", type=Path, default=Path("output"))
    avail.add_argument("--headed", action="store_true")

    url = sub.add_parser("url", help="Print the booking URL for a date")
    url.add_argument("--date", type=date.fromisoformat, default=date.today())

    bk = sub.add_parser("book", help="Watch for a free court and book it")
    when = bk.add_mutually_exclusive_group()
    when.add_argument("--date", type=date.fromisoformat, help="YYYY-MM-DD")
    when.add_argument("--day", choices=WEEKDAYS, default="friday", help="next such day (default friday)")
    bk.add_argument("--time", default="20:00", help="slot start time, HH:MM (default 20:00)")
    bk.add_argument("--interval", type=int, default=60, help="seconds between checks (min 30)")
    bk.add_argument("--stop-before", type=int, default=60,
                    help="stop watching this many minutes before the slot (default 60)")
    bk.add_argument("--confirm", action="store_true", help="actually complete the booking")
    bk.add_argument("--headed", action="store_true", help="show the browser window")
    bk.add_argument("--out", type=Path, default=Path("output"))

    args = parser.parse_args(argv)
    load_dotenv()
    cfg = Config.from_env()

    try:
        if args.command == "url":
            print(booking_url(cfg.venue, args.date))
        elif args.command == "availability":
            out = capture_availability(cfg, args.date, args.out, headless=not args.headed)
            print(f"Saved screenshot and responses to {out}")
        elif args.command == "book":
            start = time.fromisoformat(args.time)
            day = args.date or next_weekday(WEEKDAYS.index(args.day), datetime.now(), start)
            until = datetime.combine(day, start) - timedelta(minutes=args.stop_before)
            print(f"Target: {day:%A %d %b %Y} at {args.time}; watching until {until:%a %H:%M}."
                  f"{'' if args.confirm else ' (dry run)'}")
            ok = watch_and_book(cfg, day, to_minutes(args.time), interval=max(30, args.interval),
                                until=until, confirm=args.confirm, headless=not args.headed,
                                out=args.out / f"booking-{day.isoformat()}")
            return 0 if ok else 1
    except BlockedError as exc:
        print(exc, file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
