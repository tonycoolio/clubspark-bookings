"""Playwright helpers for the ClubSpark booking pages."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright

from .booker import BlockedError
from .config import BASE_URL, Config, booking_url


def capture_availability(cfg: Config, day: date, out_dir: Path, headless: bool = True) -> Path:
    """Open the Book-by-date page as a guest, save a screenshot and any JSON
    the page loads from ClubSpark. Returns the output directory for that day.

    The page is a JavaScript app, so the slot data arrives via XHR; saving those
    responses lets us discover the data format before writing a parser.
    """
    day_dir = out_dir / day.isoformat()
    day_dir.mkdir(parents=True, exist_ok=True)
    responses: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page(viewport={"width": 1400, "height": 1000})

        def on_response(resp):
            ctype = resp.headers.get("content-type", "")
            if resp.url.startswith(BASE_URL) and "json" in ctype:
                try:
                    responses.append({"url": resp.url, "status": resp.status, "body": resp.json()})
                except Exception:  # body not JSON after all
                    pass

        page.on("response", on_response)
        resp = page.goto(booking_url(cfg.venue, day), wait_until="networkidle", timeout=60_000)
        page.screenshot(path=str(day_dir / "page.png"), full_page=True)
        blocked = resp is not None and resp.status == 403 and "have been blocked" in page.content()
        browser.close()

    if blocked:
        raise BlockedError(
            "ClubSpark (Cloudflare) blocked this request. This happens from cloud/data-centre "
            "IPs; run the tool from a home connection instead. Screenshot: "
            f"{day_dir / 'page.png'}"
        )

    (day_dir / "responses.json").write_text(json.dumps(responses, indent=2))
    return day_dir

