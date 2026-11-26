"""Watch for a free court at a given date/time and book it."""
from __future__ import annotations

import random
import time as _time
from datetime import date, datetime
from pathlib import Path

from playwright.sync_api import BrowserContext, Page, sync_playwright

from . import selectors as S
from .config import BASE_URL, Config, booking_url
from .slots import Slot, matching


class BlockedError(RuntimeError):
    """ClubSpark's Cloudflare firewall refused the request (common from cloud IPs)."""


def _check_blocked(page: Page, status: int | None) -> None:
    if status == 403 and "have been blocked" in page.content():
        raise BlockedError(
            "ClubSpark (Cloudflare) blocked this request. This happens from cloud/data-centre "
            "IPs; run the tool from a home connection instead."
        )


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def ensure_signed_in(page: Page, cfg: Config) -> None:
    resp = page.goto(BASE_URL + S.SIGN_IN_PATH.format(venue=cfg.venue), wait_until="networkidle")
    _check_blocked(page, resp.status if resp else None)
    if page.locator(S.SIGNED_IN_MARKER).count():
        log("Already signed in (saved session).")
        return
    if not cfg.has_credentials:
        raise RuntimeError("Set CLUBSPARK_USERNAME and CLUBSPARK_PASSWORD (e.g. in .env).")
    lta = page.locator(S.LTA_SIGN_IN_BUTTON).first
    if lta.count():
        lta.click()
        page.wait_for_load_state("networkidle")
    page.locator(S.USERNAME_INPUT).first.fill(cfg.username)
    page.locator(S.PASSWORD_INPUT).first.fill(cfg.password)
    page.locator(S.SUBMIT_LOGIN).first.click()
    page.wait_for_load_state("networkidle")
    page.goto(booking_url(cfg.venue, date.today(), role="member"), wait_until="networkidle")
    if not page.locator(S.SIGNED_IN_MARKER).count():
        raise RuntimeError("Sign-in did not succeed; run with --headed to see what happened.")
    log("Signed in.")


def find_free(page: Page, cfg: Config, day: date, start_minutes: int) -> list[Slot]:
    resp = page.goto(booking_url(cfg.venue, day, role="member"), wait_until="networkidle")
    _check_blocked(page, resp.status if resp else None)
    page.reload(wait_until="networkidle")  # hash-only URL changes don't refetch
    page.wait_for_selector(S.GRID_READY, timeout=30_000)
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


def watch_and_book(cfg: Config, day: date, start_minutes: int, *, interval: int, until: datetime,
                   confirm: bool, headless: bool, out: Path) -> bool:
    out.mkdir(parents=True, exist_ok=True)
    state = out / "auth.json"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx: BrowserContext = browser.new_context(
            storage_state=str(state) if state.exists() else None,
            viewport={"width": 1400, "height": 1000},
        )
        page = ctx.new_page()
        ensure_signed_in(page, cfg)
        ctx.storage_state(path=str(state))
        hhmm = f"{start_minutes // 60:02d}:{start_minutes % 60:02d}"
        while datetime.now() < until:
            slots = find_free(page, cfg, day, start_minutes)
            if slots:
                log(f"Free court(s) at {hhmm} on {day}: {[s.court_id for s in slots]}. Booking...")
                done = book(page, slots[0], out, confirm)
                browser.close()
                return done
            wait = interval + random.uniform(0, interval * 0.2)
            log(f"No court free at {hhmm} on {day}; checking again in {wait:.0f}s.")
            _time.sleep(wait)
        log("Gave up: deadline reached with no free court.")
        browser.close()
        return False
