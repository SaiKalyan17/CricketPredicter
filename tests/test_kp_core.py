import pytest

from astrology.kp_calculations import (DASHA_YEARS, HORARY_TABLE, NAK_LEN, horary_number_longitude,
                                       kp_info)
from astrology.dasha_analysis import running_dasha
from astrology.house_cusps import house_of
from astrology.planetary_positions import manual_positions
from datetime import datetime, timedelta, timezone


def test_nakshatra_and_star():
    i = kp_info(0.0)
    assert (i.sign, i.nakshatra, i.star_lord) == ("Aries", "Ashwini", "Ketu")
    assert kp_info(NAK_LEN + 0.01).star_lord == "Venus"
    assert kp_info(359.99).nakshatra == "Revati"


def test_sub_lord_boundaries():
    # Ashwini: Ketu sub spans 7/120 of 13.333 deg = 0.7778 deg, then Venus
    assert kp_info(0.5).sub_lord == "Ketu"
    assert kp_info(0.8).sub_lord == "Venus"
    assert kp_info(0.8).sub_sub_lord in DASHA_YEARS


def test_sub_sub_lord_starts_with_sub_lord():
    i = kp_info(0.01)
    assert (i.sub_lord, i.sub_sub_lord) == ("Ketu", "Ketu")
    # second sub-sub inside Ketu sub: Venus share = 0.7778*20/120
    assert kp_info(0.7778 * 7 / 120 + 0.001).sub_sub_lord == "Venus"


def test_horary_table_has_249_rows_and_covers_zodiac():
    assert len(HORARY_TABLE) == 249
    assert HORARY_TABLE[0]["start"] == 0 and HORARY_TABLE[-1]["end"] == pytest.approx(360)
    for a, b in zip(HORARY_TABLE[:-1], HORARY_TABLE[1:]):
        assert a["end"] == pytest.approx(b["start"])


def test_horary_number_matches_table_sub_lord():
    for n in (1, 2, 100, 249):
        assert kp_info(horary_number_longitude(n)).sub_lord == HORARY_TABLE[n - 1]["sub_lord"]
    with pytest.raises(ValueError):
        horary_number_longitude(250)


def test_house_of_wraparound():
    cusps = [350 + 30 * i for i in range(12)]
    cusps = [c % 360 for c in cusps]
    assert house_of(355, cusps) == 1
    assert house_of(10, cusps) == 1
    assert house_of(25, cusps) == 2


def test_manual_positions_validation_and_ketu():
    p = manual_positions({"Rahu": 10.0})
    assert p["Ketu"].longitude == pytest.approx(190.0)
    with pytest.raises(ValueError):
        manual_positions({"Sun": 400})


def test_dasha_start_of_ashwini_and_total_cycle():
    ref = datetime(2026, 1, 1, tzinfo=timezone.utc)
    d = running_dasha(0.0, ref, ref)
    assert d["Mahadasha"]["lord"] == "Ketu" and d["Bhukti"]["lord"] == "Ketu"
    later = running_dasha(0.0, ref, ref + timedelta(days=7 * 365.25 + 1))
    assert later["Mahadasha"]["lord"] == "Venus"


def test_dasha_balance_mid_nakshatra():
    ref = datetime(2026, 1, 1, tzinfo=timezone.utc)
    d = running_dasha(NAK_LEN / 2, ref, ref)
    md = d["Mahadasha"]
    assert (ref - md["start"]).days == pytest.approx(3.5 * 365.25, abs=1)
