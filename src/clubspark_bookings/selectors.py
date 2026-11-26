"""Every CSS selector and URL path that depends on ClubSpark's page layout.

Sign-in, the booking grid and free/taken slots are confirmed on the live site.
The booking pop-up's continue button and the confirm button are also CONFIRMED by a
dry run on 26 Nov 2026 (Court 1, 27 Nov 14:30): it reached "Confirm your booking"
(court, date, time, 30 mins, total cost) with its "Confirm" button found by
CONFIRM_BOOKING. No selector changes were needed.
"""

# Slots on the Book-by-date grid carry
#   data-test-id="booking-<courtId>|<YYYY-MM-DD>|<minutes>"   (minutes after midnight; 20:00 -> 1200)
# CONFIRMED (26 Nov 2026, signed in as a member):
#   taken: <a class="edit-booking" ...>  text like "20:00 - 21:00 Booked"
#   free:  <a class="book-interval not-booked" ...>  text "FREE"  (one per 30-minute start)
SLOT_ATTR = "data-test-id"
ANY_SLOT = "[data-test-id^='booking-']"
FREE_SLOT = "a.book-interval.not-booked[data-test-id^='booking-']"

# Grid has finished rendering (any slot, booked or not).
GRID_READY = ANY_SLOT

# Booking pop-up after clicking a slot: "<date>, 08:30 to [09:00 v]" then "For 30 minutes".
# CONFIRMED (26 Nov 2026): the "to" drop-down is a select2-wrapped <select id="booking-duration">
# whose option values are end times in minutes after midnight, offered only up to the
# court's next booking.
DURATION_SELECT = "select#booking-duration"
# Length label under it: "For 30 minutes", "For 1hr 0 minutes".
DURATION_TEXT = "text=/For (\\d+\\s*hrs? )?\\d+ minutes/"

# Booking pop-up's continue button.
CONTINUE_BOOKING = "#submit-booking, button:has-text('Continue booking')"

# Final confirmation page.
CONFIRM_BOOKING = "button:has-text('Confirm and pay'), button:has-text('Confirm booking'), #paynow"

# Sign-in (confirmed from a recorded login on 26 Nov 2026):
#   1. /ShootersHillLTC/Account/SignIn redirects to auth.clubspark.uk/account/signin,
#      whose "Login" button (button[name=idp]) goes to the LTA login;
#   2. mylta.my.site.com/s/login/ (Salesforce): Username box (placeholder only, no name),
#      password box, and a type=button "Log in" with no surrounding <form>;
#   3. back to clubspark.lta.org.uk.
SIGN_IN_PATH = "/{venue}/Account/SignIn"
LTA_SIGN_IN_BUTTON = "button[name='idp']"
USERNAME_INPUT = ("input[placeholder*='Username' i], input[name*='user' i], input[id*='user' i], "
                  "input[type='email']")
PASSWORD_INPUT = "input[type='password'], input[placeholder*='Password' i]"
REMEMBER_ME = "input#rememberMe"
SUBMIT_LOGIN = ("button:text-is('Log in'), button:text-is('Login'), button[type='submit'], "
                "input[type='submit'], button:has-text('Sign in')")
LOGIN_RETURN_URL = "**/clubspark.lta.org.uk/**"

# Header shows "Sign in" / "Register" links only when signed out.
HEADER = ".ui-header-v2-title-anchor"
SIGN_IN_LINK = "a[href*='/Account/SignIn']"
SIGNED_IN_MARKER = "a:has-text('Sign out'), a:has-text('Log out'), a[href*='SignOut']"

# Cloudflare "Performing security verification / Verify you are human" page, shown
# instead of the site after many requests in a short time (seen 26 Nov 2026).
CLOUDFLARE_CHECK = ("iframe[src*='challenges.cloudflare.com'], #challenge-form, "
                    ":text('Performing security verification'), :text('Verify you are human')")

# Cookie banner (Osano) that can cover the page.
COOKIE_REJECT = "button.osano-cm-denyAll"
