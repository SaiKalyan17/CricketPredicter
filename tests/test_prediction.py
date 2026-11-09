import pytest

from astrology.horary_analysis import csl_rows
from astrology.significators import planet_significations
from config import DEFAULT_WEIGHTS, HouseRules
from prediction.match_prediction import analyze
from prediction.scoring_engine import combine, normalize, score_category
from prediction.team_analysis import planet_evidence
from tests.helpers import CUSPS, DT, PLANETS, SETTINGS, manual_chart


def test_significators_levels():
    ch = manual_chart()
    sig = planet_significations(ch)
    # Sun (10 deg) sits in house 1 (cusp 5..35); occupant -> house 1 present
    assert 1 in sig["Sun"]
    # cusp-1 owner is Mars (Aries cusp at 5 deg) -> Mars signifies house 1
    assert 1 in sig["Mars"]


def test_csl_rows_structure():
    ch = manual_chart()
    rows = csl_rows(ch, planet_significations(ch), HouseRules())
    assert [r["Cusp"] for r in rows] == [1, 6, 7, 10, 11]
    assert all("CSL" in r for r in rows)


def test_normalization():
    assert normalize(3, 1) == (75.0, 25.0)
    assert normalize(0, 0) is None


def _cat(name, a, b):
    return {"name": name, "available": True, "A": a, "B": b, "evidence": []}


def test_partial_data_still_picks_higher_percentage_team():
    r = combine([_cat("Dasha", 1.0, 0.0)] + [score_category(n, []) for n in DEFAULT_WEIGHTS if n != "Dasha"])
    assert r["verdict"] == "WIN" and r["pA"] > r["pB"]


def test_no_data_at_all_has_no_percentage():
    r = combine([score_category(n, []) for n in DEFAULT_WEIGHTS])
    assert r["verdict"] == "UNCERTAIN" and r["pA"] is None


def test_clear_support_wins_and_swap_is_symmetric():
    cats = [_cat(n, 0.9, 0.3) for n in DEFAULT_WEIGHTS]
    swapped = [_cat(n, 0.3, 0.9) for n in DEFAULT_WEIGHTS]
    r, s = combine(cats), combine(swapped)
    assert r["verdict"] == "WIN" and s["verdict"] == "LOSS"
    assert r["pA"] == pytest.approx(s["pB"])


def test_weights_configurable_and_zero_weight_ignored():
    cats = [_cat("Dasha", 1.0, 0.0), _cat("Transits", 0.0, 1.0)]
    w = {"Dasha": 0.0, "Transits": 1.0}
    assert combine(cats, w, min_coverage=0.5)["verdict"] == "LOSS"


def test_house_rules_symmetric_under_swap():
    ch = manual_chart()
    sig = planet_significations(ch)
    r = HouseRules()
    s = HouseRules(own_a=7, own_b=1)
    for p in ch.planets:
        e1, e2 = planet_evidence("x", p, "r", sig, r), planet_evidence("x", p, "r", sig, s)
        if e1:
            assert e1["A"] == e2["B"] and e1["B"] == e2["A"]


def _form(**kw):
    f = {"team_a": "X", "team_b": "Y", "match_dt": DT, "lat": 19.0, "lon": 72.0, "hor_dt": DT,
         "hor_lat": 19.0, "hor_lon": 72.0, "hor_number": 1, "settings": SETTINGS,
         "manual": {"match": {"planets": PLANETS, "cusps": CUSPS},
                    "horary": {"planets": PLANETS, "cusps": CUSPS}}}
    f.update(kw)
    return f


def test_full_pipeline_manual_and_team_swap_no_directional_bias():
    a = analyze(_form())
    b = analyze(_form(team_a="Y", team_b="X", rules=HouseRules(own_a=7, own_b=1)))
    assert a["result"]["coverage"] > 0.9
    if a["result"]["pA"] is not None:
        assert a["result"]["pA"] == pytest.approx(b["result"]["pB"])
        assert a["result"]["pB"] == pytest.approx(b["result"]["pA"])


def test_pipeline_reports_unavailable_without_data():
    r = analyze(_form(manual={}, hor_dt=None))
    from astrology import planetary_positions as pp
    if not pp.HAVE_SWE:
        assert r["unavailable"] and r["result"]["verdict"] == "UNCERTAIN"
    assert any("Second innings" in u for u in r["unavailable"])


def test_toss_rules_win_lose_and_connection():
    from prediction.toss_prediction import evaluate_toss_houses as ev
    assert ev([1, 6, 10])["queried_wins"]
    assert ev([2, 3])["queried_wins"]
    assert not ev([4, 5, 7, 12])["queried_wins"]
    assert not ev([1, 2])["queried_wins"]          # win houses but no 3/6/10/11 connection
    assert not ev([3, 4, 5])["queried_wins"]       # lose group larger
    assert not ev([])["queried_wins"]


def test_batting_first_from_toss_winner():
    from prediction.toss_prediction import predict_batting_first as pb
    n = ("A", "B")
    assert pb("A", n, "A")["batting_first"] == "A"
    assert pb("A", n, "B")["batting_first"] == "B"
    assert pb("A", n, "Balanced")["batting_first"] == "A"
