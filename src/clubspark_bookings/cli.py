"""Command line entry point: `python -m clubspark_bookings.cli availability --date 2026-11-26`."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import sys

from .browser import BlockedError, capture_availability
from .config import Config, booking_url


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="clubspark")
    sub = parser.add_subparsers(dest="command", required=True)

    avail = sub.add_parser("availability", help="Capture the guest booking page for a date")
    avail.add_argument("--date", type=date.fromisoformat, default=date.today())
    avail.add_argument("--out", type=Path, default=Path("output"))
    avail.add_argument("--headed", action="store_true")

    url = sub.add_parser("url", help="Print the booking URL for a date")
    url.add_argument("--date", type=date.fromisoformat, default=date.today())

    args = parser.parse_args(argv)
    cfg = Config.from_env()

    if args.command == "url":
        print(booking_url(cfg.venue, args.date))
    elif args.command == "availability":
        try:
            out = capture_availability(cfg, args.date, args.out, headless=not args.headed)
        except BlockedError as exc:
            print(exc, file=sys.stderr)
            return 2
        print(f"Saved screenshot and responses to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
