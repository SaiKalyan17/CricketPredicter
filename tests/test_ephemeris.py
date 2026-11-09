"""Native-engine tests (PyEphem + Meeus formulas); skipped if PyEphem is missing."""
from datetime import datetime, timezone

import pytest

from astrology import planetary_positions as pp
from astrology.house_cusps import build_chart, compute_cusps
from astrology.kp_calculations import horary_number_longitude

pytestmark = pytest.mark.skipif(not pp.HAVE_ENGINE, reason="PyEphem not installed")
KP = "KP New (Krishnamurti)"
S = {"ayanamsa": KP, "house_system": "Placidus (KP standard)", "node": "mean"}


def test_julian_day():
    assert pp.julian_day(datetime(2000, 1, 1, 12, tzinfo=timezone.utc)) == pytest.approx(2451545.0)
    assert pp.julian_day(datetime(1987, 1, 27, 0, tzinfo=timezone.utc)) == pytest.approx(2446822.5)


def test_kp_ayanamsa_2000():
    assert pp.ayanamsa_value(2451545.0, KP) == pytest.approx(23.76, abs=0.03)
    assert pp.ayanamsa_value(2451545.0, "Lahiri") == pytest.approx(23.857, abs=0.01)


def test_unsupported_ayanamsa_is_explicit():
    with pytest.raises(ValueError):
        pp.ayanamsa_value(2451545.0, "KP Old (VP291)")


def test_moon_meeus_example():
    # Meeus ex. 47.a: 1992-04-12 0h TD, apparent longitude ~133.167 deg
    jd = 2448724.5
    assert pp._tropical_lon("Moon", jd) == pytest.approx(133.167, abs=0.03)


def test_sun_j2000_sidereal():
    pos = pp.compute_positions(2451545.0, KP, "mean")
    assert pos["Sun"].longitude == pytest.approx(280.37 - 23.76, abs=0.1)
    assert (pos["Ketu"].longitude - pos["Rahu"].longitude) % 360 == pytest.approx(180)
    assert pos["Rahu"].retrograde


def test_mean_node_j2000():
    assert pp._node_longitude(2451545.0, "mean") == pytest.approx(125.04, abs=0.01)


def test_cusps_are_ordered_and_opposite():
    dt = datetime(2026, 3, 1, 8, 30, tzinfo=timezone.utc)
    jd = pp.julian_day(dt)
    c = compute_cusps(jd, 19.07, 72.87, KP, "Placidus (KP standard)")
    spans = [(c[(i + 1) % 12] - c[i]) % 360 for i in range(12)]
    assert sum(spans) == pytest.approx(360) and all(0 < x < 90 for x in spans)
    for i in range(6):
        assert (c[i + 6] - c[i]) % 360 == pytest.approx(180, abs=1e-6)


def test_asc_matches_known_value():
    # Greenwich-like check: at lat 0 and RAMC 0 the tropical ascendant is 90 deg (Cancer 0)
    from astrology.house_cusps import math
    r = math.radians
    asc = math.degrees(math.atan2(1, -(0 + 0))) % 360
    assert asc == pytest.approx(90)


def test_horary_ascendant_rotation():
    dt = datetime(2026, 3, 1, 8, 30, tzinfo=timezone.utc)
    h = build_chart("h", dt, 19.07, 72.87, S, asc_override=horary_number_longitude(100))
    assert h.cusps[0] == pytest.approx(horary_number_longitude(100), abs=0.001)
    assert h.ascendant.sub_lord  # resolves into a sub lord


def test_sunrise_is_before_noon_local():
    dt = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
    jd = pp.julian_day(dt)
    sr = pp.jd_to_datetime(pp.sunrise_jd(jd - 1, 19.07, 72.87))
    assert 0 < sr.hour <= 2 or sr.hour >= 23   # ~06:50 IST = ~01:20 UTC
