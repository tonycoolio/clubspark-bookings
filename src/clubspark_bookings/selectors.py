"""Every CSS selector and URL path that depends on ClubSpark's page layout.

UNVERIFIED: these are based on ClubSpark's usual booking markup and have not yet
been checked against the live Shooters Hill pages (ClubSpark blocks cloud IPs).
Run `clubspark book --headed` (dry run) once and fix anything that doesn't match.
"""

# Bookable slots on the Book-by-date grid. ClubSpark renders free slots as
#   <a class="book-interval not-booked" data-test-id="booking-<courtId>|<YYYY-MM-DD>|<minutes>">
# where <minutes> is the start time in minutes after midnight (20:00 -> 1200).
FREE_SLOT = "a.book-interval.not-booked[data-test-id^='booking-']"
SLOT_ATTR = "data-test-id"

# Grid has finished rendering (any slot, booked or not).
GRID_READY = ".book-interval"

# Booking pop-up after clicking a slot, and its continue button.
CONTINUE_BOOKING = "#submit-booking, button:has-text('Continue booking')"

# Final confirmation page.
CONFIRM_BOOKING = "button:has-text('Confirm and pay'), button:has-text('Confirm booking'), #paynow"

# Sign-in.
SIGN_IN_PATH = "/{venue}/Account/SignIn"
LTA_SIGN_IN_BUTTON = "button:has-text('LTA'), a:has-text('Sign in with LTA'), a:has-text('LTA')"
USERNAME_INPUT = "input[type='email'], input[name*='user' i], input[id*='user' i], input[name*='email' i]"
PASSWORD_INPUT = "input[type='password']"
SUBMIT_LOGIN = "button[type='submit'], input[type='submit'], button:has-text('Log in'), button:has-text('Sign in')"
SIGNED_IN_MARKER = "a:has-text('Sign out'), a:has-text('Log out'), a[href*='SignOut']"
