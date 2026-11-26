from datetime import date

from playwright.sync_api import sync_playwright

from clubspark_bookings import selectors as S
from clubspark_bookings.booker import on_cloudflare_check
from clubspark_bookings.slots import matching

# Markup recorded on the live grid (signed in as a member), 26 Nov 2026.
GRID = """
<a data-test-id="booking-c1|2026-11-27|1140" class="edit-booking" href="#">19:00 - 20:00 Booked</a>
<a data-test-id="booking-c1|2026-11-27|1200" class="book-interval not-booked" href="#">FREE</a>
<a data-test-id="booking-c2|2026-11-27|1200" class="edit-booking" href="#">20:00 - 21:00 Booked</a>
<a data-test-id="booking-c3|2026-11-27|1230" class="book-interval not-booked" href="#">FREE</a>
"""

CLOUDFLARE = """
<h1>clubspark.lta.org.uk</h1><h2>Performing security verification</h2>
<iframe src="https://challenges.cloudflare.com/cdn-cgi/challenge-platform/x"></iframe>
"""


def with_page(html, fn):
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page()
        page.set_content(html)
        try:
            return fn(page)
        finally:
            b.close()


def test_free_slot_selector_matches_only_free_slots():
    ids = with_page(GRID, lambda page: [e.get_attribute(S.SLOT_ATTR)
                                        for e in page.locator(S.FREE_SLOT).all()])
    assert [s.court_id for s in matching(ids, date(2026, 11, 27), 1200)] == ["c1"]


def test_cloudflare_check_detected():
    assert with_page(CLOUDFLARE, on_cloudflare_check) is True
    assert with_page(GRID, on_cloudflare_check) is False


# Mimics the "Make a booking" pop-up recorded on 26 Nov 2026: a select2-hidden <select>.
POPUP = """
<p>Friday 4th December 2026, 20:00 to
<select id="booking-duration" class="select2-hidden-accessible"
        style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)"
        onchange="const m=this.value-1200; document.getElementById('len').textContent=
          'For '+(m>=60 ? Math.floor(m/60)+'hr '+(m%60) : m)+' minutes'">
  <option value="1230">20:30</option><option value="1260">21:00</option><option value="1290">21:30</option>
</select></p>
<p id="len">For 30 minutes</p>
<button id="submit-booking">Continue booking</button>
"""


def test_choose_length_sets_an_hour():
    from clubspark_bookings.booker import choose_length
    from clubspark_bookings.slots import Slot

    slot = Slot("c1", date(2026, 12, 4), 1200)
    assert with_page(POPUP, lambda page: choose_length(page, slot, 60)) == 60
    assert with_page(POPUP, lambda page: choose_length(page, slot, 30)) == 30
