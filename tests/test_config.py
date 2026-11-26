from datetime import date

from clubspark_bookings.config import Config, booking_url


def test_booking_url_matches_clubspark_format():
    assert (
        booking_url("ShootersHillLTC", date(2026, 11, 26))
        == "https://clubspark.lta.org.uk/ShootersHillLTC/Booking/BookByDate#?date=2026-11-26&role=guest"
    )


def test_config_from_env(monkeypatch):
    monkeypatch.setenv("CLUBSPARK_VENUE", "SomeClub")
    monkeypatch.delenv("CLUBSPARK_USERNAME", raising=False)
    monkeypatch.delenv("CLUBSPARK_PASSWORD", raising=False)
    cfg = Config.from_env()
    assert cfg.venue == "SomeClub"
    assert not cfg.has_credentials


def test_browser_launches():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content("<h1>ok</h1>")
        assert page.inner_text("h1") == "ok"
        browser.close()
