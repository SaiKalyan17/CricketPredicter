"""KP horary: cusp sub lord (CSL) analysis for houses 1, 6, 7, 10, 11."""
from astrology.house_cusps import Chart
from config import CSL_CUSP_WEIGHTS, HouseRules
from prediction.team_analysis import planet_evidence

CSL_HOUSES = (1, 6, 7, 10, 11)


def csl_rows(chart: Chart, sig: dict, rules: HouseRules, team_names=("Team A", "Team B")) -> list:
    rows = []
    for h in CSL_HOUSES:
        ci = chart.cusp_info[h - 1]
        p = ci.sub_lord
        pl = chart.planets.get(p)
        houses = sorted(sig.get(p, {}))
        row = {"Cusp": h, "CSL": p, "CSL star lord": pl.info.star_lord if pl else "-",
               "CSL sub lord": pl.info.sub_lord if pl else "-", "Signifies": houses}
        for t, name in zip(("A", "B"), team_names):
            row[f"{name} positive"] = sorted(set(houses) & rules.positive(t))
            row[f"{name} negative"] = sorted(set(houses) & rules.negative(t))
        rows.append(row)
    return rows


def csl_evidence(chart: Chart, sig: dict, rules: HouseRules) -> list:
    return [planet_evidence("Horary CSL", chart.cusp_info[h - 1].sub_lord, f"CSL of cusp {h}",
                            sig, rules, CSL_CUSP_WEIGHTS[h]) for h in CSL_HOUSES]


def compare_1_7(rows: list, rules: HouseRules, team_names=("Team A", "Team B")) -> str:
    r1 = next(r for r in rows if r["Cusp"] == rules.own_a)
    r7 = next(r for r in rows if r["Cusp"] == rules.own_b)
    def net(r, t):
        return len(r[f"{team_names[0 if t=='A' else 1]} positive"]) - len(r[f"{team_names[0 if t=='A' else 1]} negative"])
    a = net(r1, "A") + (-net(r7, "A"))
    b = net(r7, "B") + (-net(r1, "B"))
    if a == b:
        return "1st and 7th CSL give balanced support (no single CSL decides the result)."
    return (f"{team_names[0] if a > b else team_names[1]} has stronger 1st/7th CSL support "
            f"(indicator balance {a} vs {b}); combined with other CSLs and categories before any verdict.")
