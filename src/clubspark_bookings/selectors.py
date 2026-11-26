"""Every CSS selector and URL path that depends on ClubSpark's page layout.

UNVERIFIED: these are based on ClubSpark's usual booking markup and have not yet
been checked against the live Shooters Hill pages (ClubSpark blocks cloud IPs).
Run `clubspark book --headed` (dry run) once and fix anything that doesn't match.
"""

# Slots on the Book-by-date grid carry
#   data-test-id="booking-<courtId>|<YYYY-MM-DD>|<minutes>"   (minutes after midnight; 20:00 -> 1200)
# CONFIRMED (26 Nov 2026): taken slots are <a class="edit-booking" ...>, text like "20:00 - 21:00 Booked".
# NOT YET SEEN: free slots. Assumed to be any slot that isn't marked as taken.
SLOT_ATTR = "data-test-id"
ANY_SLOT = "[data-test-id^='booking-']"
FREE_SLOT = ("a.book-interval.not-booked[data-test-id^='booking-'], "
             "[data-test-id^='booking-']:not(.edit-booking):not(.booked)")

# Grid has finished rendering (any slot, booked or not).
GRID_READY = ANY_SLOT

# Booking pop-up after clicking a slot, and its continue button.
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

# Cookie banner (Osano) that can cover the page.
COOKIE_REJECT = "button.osano-cm-denyAll"
