from datetime import date, datetime, time

from clubspark_bookings.slots import matching, next_weekday, parse_slot, to_minutes


def test_parse_slot():
    s = parse_slot("booking-abc-123|2026-11-27|1200")
    assert s.court_id == "abc-123" and s.day == date(2026, 11, 27) and s.start == time(20, 0)
    assert parse_slot("booking-bad") is None
    assert parse_slot("other|2026-11-27|1200") is None
    assert parse_slot("booking-x|notadate|1200") is None


def test_matching_filters_day_and_time():
    ids = [
        "booking-c1|2026-11-27|1200",
        "booking-c2|2026-11-27|1140",
        "booking-c3|2026-11-28|1200",
        "booking-c4|2026-11-27|1200",
    ]
    assert [s.court_id for s in matching(ids, date(2026, 11, 27), to_minutes("20:00"))] == ["c1", "c4"]


def test_next_friday():
    fri = 4
    thu = datetime(2026, 11, 26, 9, 0)
    assert next_weekday(fri, thu, time(20)) == date(2026, 11, 27)
    assert next_weekday(fri, datetime(2026, 11, 27, 19, 0), time(20)) == date(2026, 11, 27)
    assert next_weekday(fri, datetime(2026, 11, 27, 20, 30), time(20)) == date(2026, 12, 4)


def test_release_plan_thursday_releases_friday_week():
    from clubspark_bookings.slots import release_plan

    target, release = release_plan(datetime(2026, 11, 26, 19, 55), time(20), 8)
    assert target == date(2026, 12, 4) and target.weekday() == 4
    assert release == datetime(2026, 11, 26, 20, 0)


def test_longest_first_prefers_courts_free_for_the_hour():
    from clubspark_bookings.slots import longest_first

    ids = [
        "booking-short|2026-12-04|1200",                                 # 20:30 taken
        "booking-long|2026-12-04|1200", "booking-long|2026-12-04|1230",  # free 20:00-21:00
        "booking-other|2026-12-05|1230",                                 # other day ignored
    ]
    assert [s.court_id for s in longest_first(ids, date(2026, 12, 4), 1200, 60)] == ["long", "short"]


def test_pick_end():
    from clubspark_bookings.slots import pick_end

    assert pick_end([1230, 1260, 1290], 1200, 60) == 1260
    assert pick_end([1230], 1200, 60) == 1230          # only 30 min free on this court
    assert pick_end([], 1200, 60) is None


def test_parse_length():
    from clubspark_bookings.slots import parse_length

    assert parse_length("For 30 minutes") == 30
    assert parse_length("For 1hr 0 minutes") == 60
    assert parse_length("For 1hr 30 minutes") == 90
    assert parse_length("Free") is None


def test_describe_booking():
    from clubspark_bookings.slots import describe_booking

    # Text of the real "Your booking has been confirmed" page, 26 Nov 2026.
    booked = ("Your booking has been confirmed\nWe've emailed the confirmation.\nBooking details\n"
              "Court 5\n04 Dec 2026, 20:00 - 20:30\nAdd booking to your calendar")
    assert describe_booking(booked) == "Court 5, 20:00-20:30"
    confirm = "Resource details\nCourt 4\n28 November 2026, 16:00 - 17:00 · 60 mins"
    assert describe_booking(confirm) == "Court 4, 16:00-17:00"
    assert describe_booking("nothing here") is None
