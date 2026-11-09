from datetime import date, datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def validate_lat_lon(lat, lon):
    lat, lon = float(lat), float(lon)
    if not -90 <= lat <= 90:
        raise ValueError("Latitude must be between -90 and 90")
    if not -180 <= lon <= 180:
        raise ValueError("Longitude must be between -180 and 180")
    return lat, lon


def validate_timezone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, KeyError):
        raise ValueError(f"Unknown timezone '{name}' (use IANA names, e.g. Asia/Kolkata)")


def validate_horary_number(n) -> int:
    n = int(n)
    if not 1 <= n <= 249:
        raise ValueError("Horary number must be between 1 and 249")
    return n


def validate_longitude_table(table: dict) -> dict:
    for k, v in table.items():
        lon = v[0] if isinstance(v, (tuple, list)) else v
        if lon is None or not 0 <= float(lon) < 360:
            raise ValueError(f"{k}: longitude must be in [0, 360)")
    return table
