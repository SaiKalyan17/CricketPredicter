"""House cusps (KP: Placidus, sidereal), Chart assembly, house placement."""
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from astrology import planetary_positions as pp
from astrology.kp_calculations import KPInfo, kp_info
from config import HOUSE_SYSTEMS


@dataclass
class Chart:
    label: str
    local_dt: Optional[datetime]
    jd: Optional[float]
    lat: float
    lon: float
    planets: dict
    cusps: list                     # 12 sidereal longitudes, index 0 = house 1
    cusp_info: list = field(default_factory=list)
    settings: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)

    @property
    def ascendant(self) -> KPInfo:
        return self.cusp_info[0]

    def house_of(self, lon: float) -> int:
        return house_of(lon, self.cusps)


def house_of(lon: float, cusps: list) -> int:
    lon %= 360
    for i in range(12):
        a, b = cusps[i] % 360, cusps[(i + 1) % 12] % 360
        if (a <= lon < b) if a < b else (lon >= a or lon < b):
            return i + 1
    return 12


def _obliquity_nutation(jd):
    T = pp._T(jd)
    r = math.radians
    eps0 = 23.439291111 - 0.013004167 * T - 1.64e-7 * T * T + 5.04e-7 * T ** 3
    om = 125.04 - 1934.136 * T
    L = 280.4665 + 36000.7698 * T
    Lp = 218.3165 + 481267.8813 * T
    dpsi = (-17.20 * math.sin(r(om)) - 1.32 * math.sin(r(2 * L)) - 0.23 * math.sin(r(2 * Lp))
            + 0.21 * math.sin(r(2 * om))) / 3600
    deps = (9.20 * math.cos(r(om)) + 0.57 * math.cos(r(2 * L)) + 0.10 * math.cos(r(2 * Lp))
            - 0.09 * math.cos(r(2 * om))) / 3600
    return eps0 + deps, dpsi


def ramc(jd, lon):
    """Apparent local sidereal time in degrees (RAMC)."""
    T = pp._T(jd)
    gmst = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * T * T - T ** 3 / 38710000
    eps, dpsi = _obliquity_nutation(jd)
    return (gmst + dpsi * math.cos(math.radians(eps)) + lon) % 360


def _placidus_cusp(theta, eps, phi, frac, above):
    """frac: 1/3 or 2/3 (counted from MC for 11/12, from IC side for 3/2)."""
    r, d = math.radians, math.degrees
    lam = None
    ra = theta + (30 if above else 150)
    for _ in range(60):
        lam = math.atan2(math.sin(r(ra)), math.cos(r(ra)) * math.cos(r(eps)))
        dec = math.asin(math.sin(r(eps)) * math.sin(lam))
        x = -math.tan(r(phi)) * math.tan(dec)
        if abs(x) >= 1:
            raise ValueError("Placidus houses undefined at this latitude/time (circumpolar); "
                             "use Equal or Whole Sign, or enter cusps manually")
        dsa = d(math.acos(x))
        new = theta + frac * dsa if above else theta + 180 - frac * (180 - dsa)
        if abs(((new - ra + 180) % 360) - 180) < 1e-9:
            ra = new
            break
        ra = new
    lam = math.atan2(math.sin(r(ra)), math.cos(r(ra)) * math.cos(r(eps)))
    return d(lam) % 360


def compute_cusps(jd, lat, lon, ayanamsa, house_system, ephe_path=None) -> list:
    """Sidereal cusps 1..12. Supports Placidus, Equal, Whole Sign."""
    pp.require_engine()
    code = HOUSE_SYSTEMS[house_system]
    r, d = math.radians, math.degrees
    eps, _ = _obliquity_nutation(jd)
    th = ramc(jd, lon)
    asc = d(math.atan2(math.cos(r(th)), -(math.sin(r(th)) * math.cos(r(eps))
                                          + math.tan(r(lat)) * math.sin(r(eps))))) % 360
    mc = d(math.atan2(math.sin(r(th)), math.cos(r(th)) * math.cos(r(eps)))) % 360
    if code == "P":
        c11 = _placidus_cusp(th, eps, lat, 1 / 3, True)
        c12 = _placidus_cusp(th, eps, lat, 2 / 3, True)
        c3 = _placidus_cusp(th, eps, lat, 1 / 3, False)
        c2 = _placidus_cusp(th, eps, lat, 2 / 3, False)
        trop = [asc, c2, c3, (mc + 180) % 360, (c11 + 180) % 360, (c12 + 180) % 360,
                (asc + 180) % 360, (c2 + 180) % 360, (c3 + 180) % 360, mc, c11, c12]
    elif code == "E":
        trop = [(asc + 30 * i) % 360 for i in range(12)]
    elif code == "W":
        s0 = (asc // 30) * 30
        trop = [(s0 + 30 * i) % 360 for i in range(12)]
    else:
        raise ValueError(f"House system '{house_system}' is not supported")
    ay = pp.ayanamsa_value(jd, ayanamsa)
    return [(c - ay) % 360 for c in trop]


def time_for_ascendant(jd, lat, lon, target, ayanamsa, house_system, ephe_path=None) -> float:
    """JD within +-0.5 day at which the sidereal ascendant equals `target` (horary-number method)."""
    def f(t):
        a = compute_cusps(t, lat, lon, ayanamsa, house_system, ephe_path)[0]
        return ((a - target + 180) % 360) - 180

    n = 100
    ts = [jd - 0.5 + i / n for i in range(n + 1)]
    best = None
    for a, b in zip(ts[:-1], ts[1:]):
        fa, fb = f(a), f(b)
        if fa <= 0 < fb and abs(fa) < 90 and abs(fb) < 90:
            if best is None or abs((a + b) / 2 - jd) < abs((best[0] + best[1]) / 2 - jd):
                best = (a, b)
    if best is None:
        raise ValueError("Could not locate ascendant for horary number at this latitude")
    lo, hi = best
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) <= 0 else (lo, mid)
    return (lo + hi) / 2


def build_chart(label, local_dt, lat, lon, settings, manual_planets=None, manual_cusps=None,
                asc_override: Optional[float] = None) -> Chart:
    """Automatic calculation needs PyEphem; otherwise manual data is required.
    asc_override: horary ascendant (planets at local_dt, cusps rotated to that ascendant)."""
    notes = []
    ay, hs = settings["ayanamsa"], settings["house_system"]
    eph = settings.get("ephe_path")
    jd = pp.julian_day(local_dt) if (local_dt and pp.HAVE_ENGINE) else None
    if manual_planets:
        planets = pp.manual_positions(manual_planets)
    else:
        pp.require_engine()
        planets = pp.compute_positions(jd, ay, settings.get("node", "true"), eph)
    if manual_cusps:
        if len(manual_cusps) != 12:
            raise ValueError("Exactly 12 cusp longitudes required")
        cusps = [float(c) % 360 for c in manual_cusps]
    else:
        pp.require_engine()
        if asc_override is not None:
            jd_h = time_for_ascendant(jd, lat, lon, asc_override, ay, hs, eph)
            cusps = compute_cusps(jd_h, lat, lon, ay, hs, eph)
            notes.append("Cusps computed for the horary-number ascendant; planets at question time.")
        else:
            cusps = compute_cusps(jd, lat, lon, ay, hs, eph)
    return Chart(label, local_dt, jd, lat, lon, planets, cusps, [kp_info(c) for c in cusps],
                 dict(settings), notes)
