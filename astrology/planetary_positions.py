"""Planetary longitudes without pyswisseph.

Planets: PyEphem (VSOP87/ELP based, ~arc-second accuracy), apparent geocentric ecliptic longitude of date,
converted to sidereal with the selected ayanamsa. Lunar nodes: Meeus ch.47 (mean node exact; true node via
the main periodic corrections, ~0.1-0.3 deg). Manual input is always available. Nothing is fabricated.
"""
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from astrology.kp_calculations import KPInfo, kp_info
from config import AYANAMSAS

try:
    import ephem
except ImportError:
    ephem = None

HAVE_ENGINE = ephem is not None
HAVE_SWE = HAVE_ENGINE            # backwards-compatible alias used by UI/tests
DUBLIN_OFFSET = 2415020.0         # JD of ephem's date zero


class EphemerisUnavailable(RuntimeError):
    pass


@dataclass
class Position:
    name: str
    longitude: float
    retrograde: bool
    info: KPInfo
    source: str = "ephem"


def require_engine():
    if not HAVE_ENGINE:
        raise EphemerisUnavailable("PyEphem is not installed (pip install ephem); provide manual positions.")


require_swe = require_engine


def julian_day(dt: datetime) -> float:
    """Julian Day (UT) from a timezone-aware datetime (Meeus ch.7, Gregorian)."""
    u = dt.astimezone(timezone.utc)
    y, m = u.year, u.month
    d = u.day + (u.hour + u.minute / 60 + u.second / 3600 + u.microsecond / 3.6e9) / 24
    if m <= 2:
        y, m = y - 1, m + 12
    a = y // 100
    b = 2 - a + a // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5


def jd_to_datetime(jd: float) -> datetime:
    return datetime(2000, 1, 1, 12, tzinfo=timezone.utc) + timedelta(days=jd - 2451545.0)


def _T(jd):
    return (jd - 2451545.0) / 36525.0


# ---- ayanamsa ----------------------------------------------------------------------------------
# value at J1900 (JD 2415020.0) + general precession in longitude since then.
_AYAN_J1900 = {"KP New (Krishnamurti)": 22.363889, "Lahiri": 22.460148}


def ayanamsa_value(jd: float, ayanamsa: str, ephe_path=None) -> float:
    if ayanamsa not in AYANAMSAS:
        raise ValueError(f"Unsupported ayanamsa: {ayanamsa}")
    if ayanamsa not in _AYAN_J1900:
        raise ValueError(f"Ayanamsa '{ayanamsa}' is not supported without pyswisseph; "
                         f"use KP New or Lahiri, or enter sidereal positions manually")
    p = lambda T: (5028.796195 * T + 1.1054348 * T * T) / 3600.0
    return _AYAN_J1900[ayanamsa] + p(_T(jd)) - p(_T(DUBLIN_OFFSET))


# ---- lunar nodes (Meeus ch.47) -------------------------------------------------------------------
def _node_longitude(jd: float, kind: str) -> float:
    T = _T(jd)
    omega = 125.0445479 - 1934.1362891 * T + 0.0020754 * T * T + T ** 3 / 467441.0
    if kind == "mean":
        return omega % 360
    r = math.radians
    D = 297.8501921 + 445267.1114034 * T
    M = 357.5291092 + 35999.0502909 * T
    Lp = 218.3164477 + 481267.88123421 * T
    F = 93.2720950 + 483202.0175233 * T
    corr = (-1.4979 * math.sin(r(2 * (D - F))) - 0.1500 * math.sin(r(M)) - 0.1226 * math.sin(r(2 * D))
            + 0.1176 * math.sin(r(2 * F)) - 0.0801 * math.sin(r(2 * (Lp - F))))
    return (omega + corr) % 360


# ---- planets -------------------------------------------------------------------------------------
_BODIES = {"Sun": "Sun", "Moon": "Moon", "Mercury": "Mercury", "Venus": "Venus", "Mars": "Mars",
           "Jupiter": "Jupiter", "Saturn": "Saturn"}


def _tropical_lon(name: str, jd: float) -> float:
    d = ephem.Date(jd - DUBLIN_OFFSET)
    body = getattr(ephem, _BODIES[name])()
    body.compute(d, epoch=d)
    eq = ephem.Equatorial(body.g_ra, body.g_dec, epoch=d)
    return math.degrees(ephem.Ecliptic(eq, epoch=d).lon) % 360


def compute_positions(jd: float, ayanamsa: str, node: str = "true", ephe_path=None) -> dict:
    require_engine()
    ay = ayanamsa_value(jd, ayanamsa)
    out = {}
    for name in _BODIES:
        lon = _tropical_lon(name, jd)
        later = _tropical_lon(name, jd + 0.01)
        retro = ((later - lon + 180) % 360) - 180 < 0
        sid = (lon - ay) % 360
        out[name] = Position(name, sid, retro, kp_info(sid))
    rahu = (_node_longitude(jd, node) - ay) % 360
    ketu = (rahu + 180) % 360
    out["Rahu"] = Position("Rahu", rahu, True, kp_info(rahu), f"meeus-{node}-node")
    out["Ketu"] = Position("Ketu", ketu, True, kp_info(ketu), f"meeus-{node}-node")
    return out


def manual_positions(table: dict) -> dict:
    """table: {planet: longitude or (longitude, retrograde)}. Ketu derived from Rahu if absent."""
    out = {}
    for name, v in table.items():
        lon, retro = (v if isinstance(v, (tuple, list)) else (v, name in ("Rahu", "Ketu")))
        lon = float(lon)
        if not 0 <= lon < 360:
            raise ValueError(f"{name}: longitude must be in [0, 360)")
        out[name] = Position(name, lon, bool(retro), kp_info(lon), "manual")
    if "Rahu" in out and "Ketu" not in out:
        k = (out["Rahu"].longitude + 180) % 360
        out["Ketu"] = Position("Ketu", k, True, kp_info(k), "derived")
    return out


def sunrise_jd(jd_start: float, lat: float, lon: float) -> Optional[float]:
    """Next sunrise (upper limb, standard refraction) after jd_start, or None."""
    if not HAVE_ENGINE:
        return None
    try:
        o = ephem.Observer()
        o.lat, o.lon, o.elevation = str(lat), str(lon), 0
        o.date = ephem.Date(jd_start - DUBLIN_OFFSET)
        return float(o.next_rising(ephem.Sun())) + DUBLIN_OFFSET
    except Exception:  # polar day/night
        return None
