from datetime import date, datetime, time
from typing import Optional
from zoneinfo import ZoneInfo


def localize(d: date, t: time, tz: ZoneInfo) -> datetime:
    """Aware datetime in the given zone (wall-clock time interpreted in that zone)."""
    return datetime.combine(d, t.replace(tzinfo=None)).replace(tzinfo=tz)


def optional_dt(enabled: bool, d: date, t: time, tz: ZoneInfo) -> Optional[datetime]:
    return localize(d, t, tz) if enabled else None
