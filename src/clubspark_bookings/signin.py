"""Signing in to ClubSpark, plus page descriptions for debugging the flow.

Page descriptions list the visible boxes, buttons and links on a page (their
names/ids/labels only, never what has been typed into them), so they are safe to
share when fixing selectors.
"""
from __future__ import annotations

import threading
from datetime import date, datetime
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator, Page

from . import selectors as S
from .config import BASE_URL, Config, booking_url

_DESCRIBE_JS = """
() => {
  const vis = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const txt = el => (el.innerText || el.getAttribute('aria-label') || '').trim().replace(/\\s+/g, ' ').slice(0, 60);
  const out = [];
  for (const el of document.querySelectorAll('input, select, textarea, button, a[href], [role=button], [data-test-id]')) {
    if (!vis(el)) continue;
    const tag = el.tagName.toLowerCase();
    if (tag === 'input' && el.type === 'hidden') continue;
    const bits = [tag];
    if (!['input','select','textarea','button','a'].includes(tag) && el.getAttribute('role') !== 'button'
        && !el.getAttribute('data-test-id')) continue;
    for (const a of ['type', 'id', 'name', 'placeholder', 'data-test-id', 'class']) {
      const v = el.getAttribute(a); if (v) bits.push(`${a}=${JSON.stringify(v.slice(0, 80))}`);
    }
    if (tag === 'a') { try { bits.push('href=' + new URL(el.href).pathname); } catch (e) {} }
    const t = tag === 'input' || tag === 'select' || tag === 'textarea' ? '' : txt(el);
    if (t) bits.push(`text=${JSON.stringify(t)}`);
    out.push(bits.join(' '));
  }
  for (const f of document.querySelectorAll('iframe')) out.push('iframe src=' + (f.src || '').split('?')[0]);
  return out.slice(0, 200);
}
"""


def describe_page(page: Page) -> str:
    """Text description of the page's visible controls (no typed values)."""
    url = page.url.split("?")[0]
    try:
        lines = page.evaluate(_DESCRIBE_JS)
    except PlaywrightError as exc:
        lines = [f"(could not describe page: {exc.message.splitlines()[0]})"]
    return "\n".join([f"URL: {url}", f"Title: {page.title()}", *("  " + l for l in lines)])


def save_debug(page: Page, debug_dir: Path, name: str) -> Path:
    debug_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%H%M%S")
    page.screenshot(path=str(debug_dir / f"{stamp}-{name}.png"), full_page=True)
    path = debug_dir / f"{stamp}-{name}.txt"
    path.write_text(describe_page(page) + "\n")
    return path


def _visible(page: Page, selector: str) -> Locator:
    return page.locator(selector).filter(visible=True).first


def _has_visible(page: Page, selector: str) -> bool:
    return page.locator(selector).filter(visible=True).count() > 0


def fill_login_form(page: Page, cfg: Config, timeout: float = 15_000) -> None:
    """Fill a username/password form using only visible fields. Handles one-page forms
    and two-step forms (username, Next, then password)."""
    _visible(page, S.USERNAME_INPUT).fill(cfg.username, timeout=timeout)
    if not _has_visible(page, S.PASSWORD_INPUT):
        _visible(page, S.SUBMIT_LOGIN).click(timeout=timeout)
    if _has_visible(page, S.REMEMBER_ME) and not page.locator(S.REMEMBER_ME).first.is_checked():
        page.locator(S.REMEMBER_ME).first.check(timeout=timeout)
    password = _visible(page, S.PASSWORD_INPUT)
    password.fill(cfg.password, timeout=timeout)
    # Prefer the submit button in the password's own form (two-step pages have two).
    in_form = password.locator("xpath=ancestor::form[1]").locator(S.SUBMIT_LOGIN).filter(visible=True)
    (in_form.first if in_form.count() else _visible(page, S.SUBMIT_LOGIN)).click(timeout=timeout)
    page.wait_for_load_state("networkidle")


def is_signed_in(page: Page) -> bool:
    """Signed in = a sign-out link exists, or the header is drawn without a Sign in link."""
    if page.locator(S.SIGNED_IN_MARKER).count():
        return True
    return _has_visible(page, S.HEADER) and not _has_visible(page, S.SIGN_IN_LINK)


def dismiss_cookie_banner(page: Page) -> None:
    try:
        if _has_visible(page, S.COOKIE_REJECT):
            _visible(page, S.COOKIE_REJECT).click(timeout=3000)
    except PlaywrightError:
        pass


def ensure_signed_in(page: Page, cfg: Config, debug_dir: Path, log) -> None:
    from .booker import check_blocked

    resp = page.goto(booking_url(cfg.venue, date.today(), role="member"), wait_until="networkidle")
    check_blocked(page, resp.status if resp else None)
    dismiss_cookie_banner(page)
    if is_signed_in(page):
        log("Already signed in (saved session).")
        return
    if not cfg.has_credentials:
        raise RuntimeError("Not signed in. Run `clubspark login`, or set CLUBSPARK_USERNAME "
                           "and CLUBSPARK_PASSWORD in .env.")
    step = "opening the sign-in page"
    try:
        page.goto(BASE_URL + S.SIGN_IN_PATH.format(venue=cfg.venue), wait_until="networkidle")
        if _has_visible(page, S.LTA_SIGN_IN_BUTTON):
            step = "clicking the Login button on ClubSpark's sign-in page"
            _visible(page, S.LTA_SIGN_IN_BUTTON).click()
            page.wait_for_load_state("domcontentloaded")
        step = "filling in the LTA username and password"
        fill_login_form(page, cfg)
        step = "waiting to be sent back to ClubSpark after logging in"
        page.wait_for_url(S.LOGIN_RETURN_URL, timeout=45_000)
        step = "checking the sign-in worked"
        page.goto(booking_url(cfg.venue, date.today(), role="member"), wait_until="networkidle")
        if not is_signed_in(page):
            raise RuntimeError("no signed-in marker found after submitting the form")
    except (PlaywrightError, RuntimeError) as exc:
        where = save_debug(page, debug_dir, "signin-failed")
        first = getattr(exc, "message", str(exc)).splitlines()[0]
        raise RuntimeError(
            f"Sign-in failed while {step} ({first}).\n"
            f"Saved a screenshot and page description in {where.parent}/.\n"
            "Try `clubspark login` to sign in by hand once."
        ) from None
    log("Signed in.")


def interactive_login(page: Page, cfg: Config, debug_dir: Path, log) -> None:
    """Open the sign-in page in a visible browser; the person signs in by hand.
    Records a description of every page visited (no typed values) for fixing selectors."""
    from .booker import check_blocked

    done = threading.Event()

    def wait_for_enter() -> None:
        try:
            input()
        except EOFError:
            pass
        done.set()

    resp = page.goto(BASE_URL + S.SIGN_IN_PATH.format(venue=cfg.venue), wait_until="domcontentloaded")
    check_blocked(page, resp.status if resp else None)
    print("\nSign in to ClubSpark in the Chrome window that just opened.\n"
          "When you can see you are signed in, come back here and press Enter.\n", flush=True)
    threading.Thread(target=wait_for_enter, daemon=True).start()

    debug_dir.mkdir(parents=True, exist_ok=True)
    trail = debug_dir / "login-pages.txt"
    seen: list[str] = []
    n = 0
    with trail.open("w") as f:
        while not done.is_set() and not page.is_closed():
            try:
                page.wait_for_timeout(1000)
                url = page.url.split("?")[0].split("#")[0]
                if not seen or seen[-1] != url:
                    page.wait_for_load_state("domcontentloaded")
                    page.wait_for_timeout(1500)  # let the page draw its form
                    seen.append(url)
                    n += 1
                    f.write(f"=== Page {n} ===\n{describe_page(page)}\n\n")
                    f.flush()
            except PlaywrightError:
                break
        if not page.is_closed():
            page.goto(booking_url(cfg.venue, date.today(), role="member"), wait_until="networkidle")
            f.write(f"=== After sign-in: booking page ===\n{describe_page(page)}\n")
    log(f"Recorded {n} page(s) in {trail}")
