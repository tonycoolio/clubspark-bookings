"""Pure helpers for slot matching and dates (no browser; unit-tested)."""
from __future__ import annotations

import re
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


def longest_first(test_ids: list[str], day: date, start_minutes: int, minutes: int,
                  step: int = 30) -> list[Slot]:
    """Free slots starting at `start_minutes`, courts that stay free for all of `minutes`
    first (the grid has one free box per `step`-minute start)."""
    free = {(s.court_id, s.start_minutes) for s in map(parse_slot, test_ids) if s and s.day == day}

    def free_for(slot: Slot) -> int:
        t = slot.start_minutes
        while (slot.court_id, t) in free and t < slot.start_minutes + minutes:
            t += step
        return t - slot.start_minutes

    return sorted(matching(test_ids, day, start_minutes), key=free_for, reverse=True)


def pick_end(options: list[int], start_minutes: int, minutes: int) -> int | None:
    """From the pop-up's end-time options (minutes after midnight), the latest one that
    keeps the booking within `minutes`."""
    ok = [o for o in options if start_minutes < o <= start_minutes + minutes]
    return max(ok) if ok else None


def parse_length(label: str) -> int | None:
    """Minutes in the pop-up's length label: "For 30 minutes" -> 30, "For 1hr 0 minutes" -> 60."""
    m = re.search(r"(?:(\d+)\s*hrs?\s*)?(\d+)\s*minutes", label)
    return int(m.group(1) or 0) * 60 + int(m.group(2)) if m else None


def next_weekday(weekday: int, after: datetime, at: time) -> date:
    """Next date with the given weekday (Mon=0) whose `at` time hasn't passed yet."""
    days = (weekday - after.weekday()) % 7
    candidate = after.date() + timedelta(days=days)
    if days == 0 and after.time() >= at:
        candidate += timedelta(days=7)
    return candidate


def release_plan(now: datetime, opens_at: time, days_ahead: int) -> tuple[date, datetime]:
    """For a run started on release day: (date being released, release moment)."""
    release = datetime.combine(now.date(), opens_at)
    return now.date() + timedelta(days=days_ahead), release
