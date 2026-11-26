"""Configuration read from environment variables (never hard-code credentials)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date

BASE_URL = "https://clubspark.lta.org.uk"


@dataclass(frozen=True)
class Config:
    venue: str
    username: str | None = None
    password: str | None = None

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            venue=os.environ.get("CLUBSPARK_VENUE", "ShootersHillLTC"),
            username=os.environ.get("CLUBSPARK_USERNAME") or None,
            password=os.environ.get("CLUBSPARK_PASSWORD") or None,
        )

    @property
    def has_credentials(self) -> bool:
        return bool(self.username and self.password)


def booking_url(venue: str, day: date, role: str = "guest") -> str:
    """URL of the venue's Book-by-date page for a given day."""
    return f"{BASE_URL}/{venue}/Booking/BookByDate#?date={day.isoformat()}&role={role}"
