"""Pure helpers for slot matching and dates (no browser; unit-tested)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta


@dataclass(frozen=True)
class Slot:
    court_id: str
    day: date
    start_minutes: int

    @property
    def start(self) -> time:
        return time(self.start_minutes // 60, self.start_minutes % 60)


def parse_slot(test_id: str) -> Slot | None:
    """Parse 'booking-<courtId>|<YYYY-MM-DD>|<minutes>' into a Slot."""
    if not test_id or not test_id.startswith("booking-"):
        return None
    parts = test_id[len("booking-"):].split("|")
    if len(parts) != 3:
        return None
    court_id, day_s, mins_s = parts
    try:
        return Slot(court_id, date.fromisoformat(day_s), int(mins_s))
    except ValueError:
        return None


def to_minutes(hhmm: str) -> int:
    t = time.fromisoformat(hhmm)
    return t.hour * 60 + t.minute


def matching(test_ids: list[str], day: date, start_minutes: int) -> list[Slot]:
    slots = (parse_slot(t) for t in test_ids)
    return [s for s in slots if s and s.day == day and s.start_minutes == start_minutes]


def next_weekday(weekday: int, after: datetime, at: time) -> date:
    """Next date with the given weekday (Mon=0) whose `at` time hasn't passed yet."""
    days = (weekday - after.weekday()) % 7
    candidate = after.date() + timedelta(days=days)
    if days == 0 and after.time() >= at:
        candidate += timedelta(days=7)
    return candidate
