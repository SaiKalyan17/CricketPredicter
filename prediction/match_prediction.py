"""Orchestrates all analyses. Anything that cannot be computed is reported as unavailable."""
from astrology import planetary_positions as pp
from astrology.dasha_analysis import dasha_evidence, manual_dasha, running_dasha
from astrology.horary_analysis import compare_1_7, csl_evidence, csl_rows
from astrology.house_cusps import Chart, build_chart
from astrology.kp_calculations import horary_number_longitude
from astrology.ruling_planets import compare_rp, ruling_planets
from astrology.significators import planet_significations
from astrology.transit_analysis import moon_match_evidence, transit_evidence, transit_table
from config import DEFAULT_WEIGHTS, RP_REPEAT_MULTIPLIER, HouseRules
from prediction.scoring_engine import combine, score_category
from prediction.team_analysis import planet_evidence
from prediction.toss_prediction import predict_batting_first, predict_toss


def _try(unavailable, name, fn):
    try:
        return fn()
    except Exception as e:  # recorded, never silently replaced with assumed data
        unavailable.append(f"{name}: {e}")
        return None


def _favoured(cat, names):
    if not cat["available"] or cat["A"] is None or cat["B"] is None:
        return "Unavailable"
    if abs(cat["A"] - cat["B"]) < 0.05:
        return "Balanced"
    return names[0] if cat["A"] > cat["B"] else names[1]


def _innings(chart, rules, names, batting_first, which):
    sig = planet_significations(chart)
    evs = moon_match_evidence(chart, sig, rules)
    cat = score_category(f"{which} innings", evs)
    fav = _favoured(cat, names)
    note = ""
    if batting_first in ("A", "B") and fav in names:
        bat = names[0] if batting_first == "A" else names[1]
        first = which == "First"
        batting_now = bat if first else (names[1] if batting_first == "A" else names[0])
        note = f"{fav} is the {'batting' if fav == batting_now else 'bowling'} side in this innings."
    elif fav in names:
        note = "Batting order not supplied: team support shown, batting/chasing advantage not assigned."
    return {"favoured": fav, "category": cat, "note": note, "asc": chart.ascendant,
            "moon": chart.planets["Moon"].info}


def analyze(f: dict) -> dict:
    """f: form dict (see app.py). Returns the full report structure."""
    names = (f["team_a"], f["team_b"])
    rules: HouseRules = f.get("rules") or HouseRules()
    weights = f.get("weights") or DEFAULT_WEIGHTS
    settings = f["settings"]
    un, charts, cats = [], {}, []
    man = f.get("manual", {})

    def mk(key, label, dt, lat, lon, **kw):
        m = man.get(key, {})
        charts[key] = _try(un, label, lambda: build_chart(
            label, dt, lat, lon, settings, m.get("planets"), m.get("cusps"), **kw))

    mk("match", "Match chart", f["match_dt"], f["lat"], f["lon"])
    asc = _try(un, "Horary number", lambda: horary_number_longitude(f["hor_number"])) \
        if f.get("hor_dt") else None
    if f.get("hor_dt"):
        mk("horary", "Horary chart", f["hor_dt"], f["hor_lat"], f["hor_lon"], asc_override=asc)
    else:
        un.append("Horary chart: no horary date/time given")
    if f.get("inn2_dt"):
        mk("inn2", "Second-innings chart", f["inn2_dt"], f["lat"], f["lon"])

    mc, hc = charts.get("match"), charts.get("horary")
    sigs = {k: planet_significations(c) for k, c in charts.items() if c}
    rep = {"names": names, "unavailable": un, "charts": charts, "tables": {}, "notes": [],
           "provisional_first_innings": not f.get("actual_start_given", False)}

    # 1. KP house significators (match chart)
    if mc:
        evs = [planet_evidence("KP House Significators", p, "planet significator", sigs["match"], rules)
               for p in mc.planets]
        cats.append(score_category("KP House Significators", evs))
    else:
        cats.append(score_category("KP House Significators", [], "Match chart unavailable"))

    # 2. Horary CSL
    if hc:
        rep["tables"]["csl"] = csl_rows(hc, sigs["horary"], rules, names)
        rep["csl_conclusion"] = compare_1_7(rep["tables"]["csl"], rules, names)
        cats.append(score_category("Horary CSL", csl_evidence(hc, sigs["horary"], rules)))
    else:
        cats.append(score_category("Horary CSL", [], "Horary chart unavailable"))

    # 3. Ruling planets (match-time and horary-time kept separate, evaluated in their own charts)
    if mc and hc:
        mrp, hrp = ruling_planets(mc), ruling_planets(hc)
        rep["rp"] = {"match": mrp, "horary": hrp, "table": compare_rp(mrp, hrp)}
        evs = []
        for p in set(mrp["planets"]) | set(hrp["planets"]):
            rep_mult = RP_REPEAT_MULTIPLIER if p in mrp["planets"] and p in hrp["planets"] else 1.0
            for k, c in (("match", mrp), ("horary", hrp)):
                if p in c["planets"]:
                    evs.append(planet_evidence("Ruling Planets", p, f"{k}-time RP", sigs[k], rules, rep_mult))
        cats.append(score_category("Ruling Planets", evs))
    else:
        cats.append(score_category("Ruling Planets", [], "Needs both match and horary charts"))

    # 4. Transits & 6. Moon/match-time (match chart)
    if mc:
        rep["tables"]["transit"] = transit_table(mc, sigs["match"], rules)
        cats.append(score_category("Transits", transit_evidence(mc, sigs["match"], rules)))
        cats.append(score_category("Moon & Match-Time", moon_match_evidence(mc, sigs["match"], rules)))
    else:
        cats += [score_category("Transits", [], "Match chart unavailable"),
                 score_category("Moon & Match-Time", [], "Match chart unavailable")]

    # 5. Dasha (reference = horary chart Moon at question time, or manual periods)
    periods = None
    if f.get("manual_dasha") and hc:
        periods = _try(un, "Manual Dasha", lambda: manual_dasha(*f["manual_dasha"]))
    elif hc and f.get("hor_dt"):
        periods = _try(un, "Dasha", lambda: running_dasha(hc.planets["Moon"].longitude, f["hor_dt"], f["hor_dt"]))
    if periods:
        rep["dasha"] = periods
        cats.append(score_category("Dasha", dasha_evidence(periods, sigs["horary"], rules)))
    else:
        un.append("Dasha: unavailable (needs horary Moon position or manual periods)")
        cats.append(score_category("Dasha", [], "Reference data unavailable"))

    # Innings / toss
    # Toss: 3rd-house CSL rule on the horary chart (queried team = Team A); falls back to match chart.
    tchart, tkey = (hc, "horary") if hc else (mc, "match")
    batting_first = f.get("batting_first")          # optional manual override ("A"/"B")
    inn1_fav = _favoured(score_category("First innings", moon_match_evidence(mc, sigs["match"], rules)),
                         names) if mc else "Unavailable"
    if tchart:
        rep["toss"] = predict_toss(tchart, sigs[tkey], names)
        if tkey == "match":
            rep["toss"]["note"] += " (Horary chart unavailable: match chart used.)"
        rep["toss"]["bat"] = predict_batting_first(rep["toss"]["winner"], names, inn1_fav)
        if batting_first not in ("A", "B"):
            batting_first = "A" if rep["toss"]["bat"]["batting_first"] == names[0] else "B"
    else:
        un.append("Toss prediction: no horary or match chart available")
    if mc:
        rep["inn1"] = _innings(mc, rules, names, batting_first, "First")
        if rep["provisional_first_innings"]:
            rep["inn1"]["note"] += " PROVISIONAL: scheduled time used (no actual commencement time)."
    if charts.get("inn2"):
        rep["inn2"] = _innings(charts["inn2"], rules, names, batting_first, "Second")
    else:
        un.append("Second innings: no commencement time (analysis unavailable)")

    rep["result"] = combine(cats, weights)
    rep["categories"] = cats
    return rep


def report_rows(rep: dict) -> list:
    """Flat rows (category, planet, roles, A/B pos/neg) for CSV export."""
    rows = []
    for c in rep["categories"]:
        for e in c["evidence"]:
            rows.append({"category": c["name"], "planet": e["planet"], "roles": "; ".join(e["roles"]),
                         "houses": " ".join(map(str, e["houses"])), "multiplier": e["mult"],
                         "A_pos": e["A"]["pos"], "A_neg": e["A"]["neg"],
                         "B_pos": e["B"]["pos"], "B_neg": e["B"]["neg"]})
    return rows
