"""Watch for a free court at a given date/time and book it."""
from __future__ import annotations

import json
import random
import subprocess
import sys
import time as _time
from datetime import date, datetime
from pathlib import Path

from playwright.sync_api import BrowserContext, Page, sync_playwright
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from . import selectors as S
from .config import BASE_URL, Config, booking_url
from .signin import ensure_signed_in, save_debug
from .slots import Slot, matching


class BlockedError(RuntimeError):
    """ClubSpark's Cloudflare firewall refused the request (common from cloud IPs)."""


def check_blocked(page: Page, status: int | None) -> None:
    if status == 403 and "have been blocked" in page.content():
        raise BlockedError(
            "ClubSpark (Cloudflare) blocked this request. This happens from cloud/data-centre "
            "IPs; run the tool from a home connection instead."
        )


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def find_free(page: Page, cfg: Config, day: date, start_minutes: int) -> list[Slot]:
    """Load (first time) or refresh the day's grid and return free slots at the target time."""
    target = booking_url(cfg.venue, day, role="member")
    if page.url != target:
        resp = page.goto(target, wait_until="domcontentloaded")
        check_blocked(page, resp.status if resp else None)
    resp = page.reload(wait_until="domcontentloaded")  # hash-only URL changes don't refetch
    check_blocked(page, resp.status if resp else None)
    try:
        page.wait_for_selector(S.GRID_READY, timeout=15_000)
    except PlaywrightTimeout:
        return []  # grid not shown (e.g. date not released yet)
    ids = [el.get_attribute(S.SLOT_ATTR) or "" for el in page.locator(S.FREE_SLOT).all()]
    return matching(ids, day, start_minutes)


def book(page: Page, slot: Slot, out: Path, confirm: bool) -> bool:
    test_id = f"booking-{slot.court_id}|{slot.day.isoformat()}|{slot.start_minutes}"
    page.locator(f"[{S.SLOT_ATTR}='{test_id}']").first.click()
    page.locator(S.CONTINUE_BOOKING).first.click()
    page.wait_for_load_state("networkidle")
    button = page.locator(S.CONFIRM_BOOKING).first
    button.wait_for(timeout=30_000)
    page.screenshot(path=str(out / "confirmation.png"), full_page=True)
    if not confirm:
        log(f"DRY RUN: stopped at the confirmation page ({out / 'confirmation.png'}). "
            "Re-run with --confirm to book for real.")
        return False
    button.click()
    page.wait_for_load_state("networkidle")
    page.screenshot(path=str(out / "booked.png"), full_page=True)
    log(f"Clicked confirm. Check {out / 'booked.png'} and your email for the booking.")
    return True


def notify(title: str, message: str) -> None:
    """Show a desktop notification on macOS (no-op elsewhere)."""
    if sys.platform == "darwin":
        script = f'display notification {json.dumps(message)} with title {json.dumps(title)}'
        subprocess.run(["osascript", "-e", script], check=False)


def wait_until(moment: datetime, lead_seconds: float = 1.0) -> None:
    """Sleep until `lead_seconds` before `moment`."""
    remaining = (moment - datetime.now()).total_seconds() - lead_seconds
    if remaining > 0:
        log(f"Waiting {remaining:.0f}s until {moment:%H:%M:%S}...")
        _time.sleep(remaining)


def watch_and_book(cfg: Config, day: date, start_minutes: int, *, interval: float, until: datetime,
                   confirm: bool, headless: bool, out: Path, state: Path,
                   start_at: datetime | None = None) -> bool:
    """Sign in, optionally wait for `start_at` (the release moment), then poll every
    `interval` seconds until a court is free at the target time and book it."""
    out.mkdir(parents=True, exist_ok=True)
    state.parent.mkdir(parents=True, exist_ok=True)
    hhmm = f"{start_minutes // 60:02d}:{start_minutes % 60:02d}"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        try:
            ctx: BrowserContext = browser.new_context(
                storage_state=str(state) if state.exists() else None,
                viewport={"width": 1400, "height": 1000},
            )
            page = ctx.new_page()
            ensure_signed_in(page, cfg, out / "debug", log)
            ctx.storage_state(path=str(state))
            if start_at:
                find_free(page, cfg, day, start_minutes)  # warm up: page loaded before release
                wait_until(start_at)
            attempts = 0
            while datetime.now() < until:
                attempts += 1
                slots = find_free(page, cfg, day, start_minutes)
                if attempts == 1:
                    save_debug(page, out / "debug", "booking-page")
                for slot in slots:
                    log(f"Court {slot.court_id} free at {hhmm} on {day}. Booking...")
                    try:
                        return book(page, slot, out, confirm)
                    except PlaywrightError as exc:  # someone beat us to it; try the next court
                        log(f"Could not book court {slot.court_id}: {exc.message.splitlines()[0]}")
                        save_debug(page, out / "debug", f"booking-failed-{attempts}")
                        find_free(page, cfg, day, start_minutes)
                if attempts == 1 or attempts % 30 == 0:
                    log(f"No court free at {hhmm} on {day} (check {attempts}).")
                _time.sleep(interval + random.uniform(0, interval * 0.2))
            log("Gave up: deadline reached with no free court.")
            return False
        finally:
            browser.close()
