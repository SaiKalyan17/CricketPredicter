"""Ruling Planets: day lord, Moon sign/star lord, Ascendant sign/star lord."""
from datetime import datetime, timedelta, timezone

from astrology import planetary_positions as pp
from astrology.house_cusps import Chart

WEEKDAY_LORDS = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]  # Mon..Sun


def kp_day_lord(chart: Chart):
    """Day lord with the KP day starting at sunrise. Returns (lord, note)."""
    dt = chart.local_dt
    if dt is None:
        return None, "No datetime"
    if pp.HAVE_ENGINE and chart.jd is not None:
        s1 = pp.sunrise_jd(chart.jd - 1.0, chart.lat, chart.lon)
        s2 = pp.sunrise_jd(s1 + 0.01, chart.lat, chart.lon) if s1 else None
        cands = [s for s in (s1, s2) if s and s <= chart.jd]
        if cands:
            sr = pp.jd_to_datetime(max(cands))
            return WEEKDAY_LORDS[sr.astimezone(dt.tzinfo).weekday()], "sunrise-based day"
    return WEEKDAY_LORDS[dt.weekday()], "civil-midnight day (sunrise unavailable) - approximation"


def ruling_planets(chart: Chart) -> dict:
    moon = chart.planets["Moon"].info
    asc = chart.ascendant
    lord, note = kp_day_lord(chart)
    rows = [("Day Lord", lord), ("Moon Sign Lord", moon.sign_lord), ("Moon Star Lord", moon.star_lord),
            ("Ascendant Sign Lord", asc.sign_lord), ("Ascendant Star Lord", asc.star_lord)]
    return {"label": chart.label, "rows": [(r, p) for r, p in rows if p], "note": note,
            "planets": sorted({p for _, p in rows if p})}


def compare_rp(match_rp: dict, horary_rp: dict) -> list:
    """RP comparison table: planet, roles at match time, roles at horary time, repeated?"""
    planets = sorted(set(match_rp["planets"]) | set(horary_rp["planets"]))
    out = []
    for p in planets:
        m = [r for r, x in match_rp["rows"] if x == p]
        h = [r for r, x in horary_rp["rows"] if x == p]
        out.append({"Planet": p, "Match-time roles": ", ".join(m) or "-",
                    "Horary-time roles": ", ".join(h) or "-", "Repeated": bool(m and h)})
    return out
