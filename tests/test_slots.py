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
