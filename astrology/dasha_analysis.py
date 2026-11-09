"""Vimshottari Dasha / Bhukti / Antara from a reference Moon longitude."""
from datetime import datetime, timedelta

from astrology.kp_calculations import DASHA_ORDER, DASHA_YEARS, NAK_LEN, kp_info
from config import YEAR_DAYS, HouseRules
from prediction.team_analysis import planet_evidence

LEVEL_MULT = {"Mahadasha": 1.0, "Bhukti": 0.8, "Antara": 0.6}


def _children(lord: str, start: datetime, days: float):
    i = DASHA_ORDER.index(lord)
    t = start
    for k in range(9):
        c = DASHA_ORDER[(i + k) % 9]
        d = days * DASHA_YEARS[c] / 120.0
        yield c, t, t + timedelta(days=d)
        t += timedelta(days=d)


def running_dasha(moon_longitude: float, ref_dt: datetime, target_dt: datetime) -> dict:
    """Running MD/AD/PD at target_dt for a Moon longitude valid at ref_dt (tz-aware datetimes)."""
    info = kp_info(moon_longitude)
    lon = moon_longitude % 360
    elapsed = (lon - min(int(lon // NAK_LEN), 26) * NAK_LEN) / NAK_LEN
    md_lord = info.star_lord
    md_start = ref_dt - timedelta(days=elapsed * DASHA_YEARS[md_lord] * YEAR_DAYS)
    lord, start = md_lord, md_start
    for _ in range(40):   # a few cycles is plenty for any realistic target
        end = start + timedelta(days=DASHA_YEARS[lord] * YEAR_DAYS)
        if start <= target_dt < end:
            break
        start, lord = end, DASHA_ORDER[(DASHA_ORDER.index(lord) + 1) % 9]
    else:
        raise ValueError("Target outside supported Dasha range")
    out = {"Mahadasha": {"lord": lord, "start": start, "end": end}}
    cur_lord, cur_start, cur_days = lord, start, DASHA_YEARS[lord] * YEAR_DAYS
    for level in ("Bhukti", "Antara"):
        for c, s, e in _children(cur_lord, cur_start, cur_days):
            if s <= target_dt < e or c == DASHA_ORDER[(DASHA_ORDER.index(cur_lord) + 8) % 9]:
                out[level] = {"lord": c, "start": s, "end": e}
                cur_lord, cur_start, cur_days = c, s, (e - s).total_seconds() / 86400
                break
    return out


def manual_dasha(md: str, ad: str, pd_: str) -> dict:
    for p in (md, ad, pd_):
        if p not in DASHA_YEARS:
            raise ValueError(f"Unknown Dasha lord '{p}'")
    return {"Mahadasha": {"lord": md}, "Bhukti": {"lord": ad}, "Antara": {"lord": pd_}}


def dasha_evidence(periods: dict, sig: dict, rules: HouseRules) -> list:
    return [planet_evidence("Dasha", v["lord"], f"{lvl} lord", sig, rules, LEVEL_MULT[lvl])
            for lvl, v in periods.items()]
