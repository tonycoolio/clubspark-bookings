"""Command line entry point (installed as `clubspark`)."""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

from .booker import BlockedError, notify, watch_and_book
from .browser import capture_availability
from .config import Config, booking_url
from .slots import next_weekday, release_plan, to_minutes

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


def login_by_hand(cfg: Config, out: Path) -> int:
    from playwright.sync_api import sync_playwright

    from .booker import log
    from .signin import interactive_login, is_signed_in

    state = out / "auth.json"
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(viewport={"width": 1300, "height": 900})
        page = ctx.new_page()
        interactive_login(page, cfg, out / "debug", log)
        if page.is_closed():
            print("The browser was closed before sign-in finished; nothing saved.", file=sys.stderr)
            return 1
        ctx.storage_state(path=str(state))
        signed_in = is_signed_in(page)
        browser.close()
    print(f"Saved your signed-in session to {state}.")
    print("Signed in: " + ("yes" if signed_in else "couldn't confirm (that's OK; send me the file below)"))
    print(f"Please send me {out / 'debug' / 'login-pages.txt'} so I can fix automatic sign-in.")
    return 0


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
    bk.add_argument("--court", help="only this court: its id or the start of it, as in the "
                                    "page's data-test-id (Court 5 = 165f0ac2)")
    bk.add_argument("--minutes", type=int, default=60,
                    help="booking length in minutes (default 60; shorter if that's all a court has)")
    bk.add_argument("--confirm", action="store_true", help="actually complete the booking")
    bk.add_argument("--headed", action="store_true", help="show the browser window")
    bk.add_argument("--out", type=Path, default=Path("output"))

    rel = sub.add_parser("release", help="Book the moment a new day's courts are released")
    rel.add_argument("--opens-at", default="20:00", help="release time, HH:MM (default 20:00)")
    rel.add_argument("--days-ahead", type=int, default=8,
                     help="days between release and the court date (default 8: Thu -> Fri week)")
    rel.add_argument("--time", default="20:00", help="court start time, HH:MM (default 20:00)")
    rel.add_argument("--start-early", type=float, default=2.0,
                     help="minutes before the release to start checking (default 2: 19:58)")
    rel.add_argument("--poll", type=float, default=5.0,
                     help="seconds between refreshes after the release (default 5, min 3; faster "
                          "trips Cloudflare's bot check)")
    rel.add_argument("--early-poll", type=float, default=15.0,
                     help="seconds between refreshes before the release (default 15)")
    rel.add_argument("--window", type=int, default=10, help="minutes to keep trying after release")
    rel.add_argument("--now", action="store_true",
                     help="don't wait for the release time (for testing a dry run)")
    rel.add_argument("--minutes", type=int, default=60,
                    help="booking length in minutes (default 60; shorter if that's all a court has)")
    rel.add_argument("--confirm", action="store_true", help="actually complete the booking")
    rel.add_argument("--headed", action="store_true")
    rel.add_argument("--out", type=Path, default=Path("output"))

    sub.add_parser("login", help="Sign in by hand once; the session is saved for later runs")

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
            label = f"{day:%a %d %b} {args.time}" + (f" (court {args.court})" if args.court else "")
            try:
                ok = watch_and_book(cfg, day, to_minutes(args.time), interval=max(30, args.interval),
                                    until=until, confirm=args.confirm, headless=not args.headed,
                                    out=args.out / f"booking-{day.isoformat()}",
                                    state=args.out / "auth.json", minutes=args.minutes,
                                    court=args.court)
            except Exception as exc:
                notify("Court watcher stopped", f"{label}: {exc}"[:200])
                raise
            if ok:
                notify("Court booked", f"{label} at Shooters Hill. Check your email.")
            elif args.confirm:
                notify("Court watcher finished", f"{label}: no cancellation before {until:%a %H:%M}.")
            return 0 if ok else 1
        elif args.command == "login":
            return login_by_hand(cfg, Path("output"))
        elif args.command == "release":
            now = datetime.now()
            day, release = release_plan(now, time.fromisoformat(args.opens_at), args.days_ahead)
            until = release + timedelta(minutes=args.window)
            start = release - timedelta(minutes=args.start_early)
            if args.now:
                start = release = now
                until = now + timedelta(minutes=args.window)
            elif now > until:
                print(f"Too late: today's release at {args.opens_at} has passed.", file=sys.stderr)
                return 1
            label = f"{day:%a %d %b} {args.time}"
            print(f"Target: {label}, released {release:%a %d %b %H:%M:%S}; "
                  f"checking from {start:%H:%M:%S}."
                  f"{'' if args.confirm else ' (dry run)'}")
            try:
                ok = watch_and_book(cfg, day, to_minutes(args.time), interval=max(3.0, args.poll),
                                    until=until, confirm=args.confirm, headless=not args.headed,
                                    out=args.out / f"booking-{day.isoformat()}",
                                    state=args.out / "auth.json", start_at=start,
                                    release_at=release,
                                    early_interval=max(3.0, args.early_poll),
                                    minutes=args.minutes)
            except Exception as exc:
                notify("Court booking failed", f"{label}: {exc}"[:200])
                raise
            if ok:
                notify("Court booked", f"{label} at Shooters Hill. Check your email.")
            elif args.confirm:
                notify("No court booked", f"{label}: none free within {args.window} min.")
            else:
                notify("Dry run finished", f"{label}: see output/booking-{day.isoformat()}")
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
