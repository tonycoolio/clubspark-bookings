from pathlib import Path

from playwright.sync_api import sync_playwright

from clubspark_bookings.config import Config
from clubspark_bookings.signin import describe_page, fill_login_form

# Mimics what the rehearsal hit: a hidden EmailAddress box ahead of the real form.
PAGE = """
<form id="other" style="display:none"><input type="text" id="EmailAddress" name="EmailAddress"></form>
<form onsubmit="document.title = 'sent:' + u.value + ':' + pw.value.length; return false">
  <input type="text" id="u" name="username">
  <input type="password" id="pw" name="password">
  <button type="submit">Log in</button>
</form>
"""

TWO_STEP = """
<form onsubmit="return false">
  <input type="text" id="u" name="username">
  <button type="submit" onclick="document.getElementById('p').style.display='block'">Next</button>
</form>
<form id="p" style="display:none" onsubmit="document.title='sent:'+pw.value.length; return false">
  <input type="password" id="pw" name="password"><button type="submit">Sign in</button>
</form>
"""

CFG = Config(venue="X", username="someone", password="secret123")


def run(html, fn):
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page()
        page.set_content(html)
        try:
            return fn(page)
        finally:
            b.close()


def test_fill_skips_hidden_fields():
    def go(page):
        fill_login_form(page, CFG, timeout=3000)
        return page.title(), page.input_value("#EmailAddress")
    title, hidden = run(PAGE, go)
    assert title == "sent:someone:9"
    assert hidden == ""


def test_fill_two_step_form():
    def go(page):
        fill_login_form(page, CFG, timeout=3000)
        return page.title()
    assert run(TWO_STEP, go) == "sent:9"


def test_describe_page_lists_visible_controls_without_values():
    def go(page):
        page.fill("#pw", "secret123")
        return describe_page(page)
    text = run(PAGE, go)
    assert 'id="u"' in text and 'type="password"' in text and 'text="Log in"' in text
    assert "EmailAddress" not in text  # hidden
    assert "secret123" not in text


# Mimics the LTA (Salesforce) login page recorded on 26 Nov 2026: no <form>,
# Username box identified only by placeholder, type=button "Log in".
LTA_PAGE = """
<div>
  <input type="text" id="159:0" placeholder="Username" class="slds-input">
  <input type="password" id="160:0" placeholder="Password">
  <button type="button">Show</button>
  <input type="checkbox" id="rememberMe" name="rememberMe">
  <button type="button" onclick="document.title='sent:'+document.getElementById('159:0').value
     +':'+document.getElementById('rememberMe').checked">Log in</button>
  <button type="button" onclick="document.title='wrong'">Create an account</button>
</div>
"""


def test_fill_lta_salesforce_page():
    def go(page):
        fill_login_form(page, CFG, timeout=3000)
        return page.title()
    assert run(LTA_PAGE, go) == "sent:someone:true"


def test_is_signed_in_from_header():
    from clubspark_bookings.signin import is_signed_in

    out = '<a class="ui-header-v2-title-anchor" href="/X">Club</a><a href="/X/Account/SignIn">Sign in</a>'
    inn = '<a class="ui-header-v2-title-anchor" href="/X">Club</a><a href="/X/Booking/Bookings">My bookings</a>'
    assert run(out, is_signed_in) is False
    assert run(inn, is_signed_in) is True


def test_free_slot_selector_ignores_booked():
    from clubspark_bookings import selectors as S

    html = """
    <a class="edit-booking" data-test-id="booking-c1|2026-12-04|1200">20:00 - 21:00 Booked</a>
    <a class="book-interval not-booked" data-test-id="booking-c2|2026-12-04|1200">Book</a>
    """
    ids = run(html, lambda p: [e.get_attribute("data-test-id") for e in p.locator(S.FREE_SLOT).all()])
    assert ids == ["booking-c2|2026-12-04|1200"]
