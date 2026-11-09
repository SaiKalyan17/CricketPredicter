"""Transit table at a chart time (match start / innings start / toss)."""
from astrology.house_cusps import Chart
from config import HouseRules
from prediction.team_analysis import planet_evidence

FOCUS = (1, 5, 6, 7, 10, 11, 12)


def transit_table(chart: Chart, sig: dict, rules: HouseRules) -> list:
    rows = []
    for name, p in chart.planets.items():
        i = p.info
        sub_houses = sorted(sig.get(i.sub_lord, {}))
        rows.append({"Planet": name, "Longitude": round(p.longitude, 4), "Sign": i.sign,
                     "Nakshatra": i.nakshatra, "Star Lord": i.star_lord, "Sub Lord": i.sub_lord,
                     "Retro": p.retrograde, "House": chart.house_of(p.longitude),
                     "Sub lord signifies": sub_houses,
                     "Activates Team A": bool(set(sub_houses) & rules.positive("A")),
                     "Activates Team B": bool(set(sub_houses) & rules.positive("B")),
                     "Focus houses hit": sorted(set(sub_houses) & set(FOCUS))})
    return rows


def transit_evidence(chart: Chart, sig: dict, rules: HouseRules) -> list:
    """Sub lords of transiting planets other than the Moon (Moon handled in Moon/Match-Time)."""
    return [planet_evidence("Transits", p.info.sub_lord, f"sub lord of transiting {n}", sig, rules)
            for n, p in chart.planets.items() if n != "Moon"]


def moon_match_evidence(chart: Chart, sig: dict, rules: HouseRules) -> list:
    m = chart.planets["Moon"].info
    a = chart.ascendant
    return [planet_evidence("Moon & Match-Time", m.star_lord, "Moon star lord", sig, rules),
            planet_evidence("Moon & Match-Time", m.sub_lord, "Moon sub lord", sig, rules),
            planet_evidence("Moon & Match-Time", a.star_lord, "Ascendant star lord", sig, rules),
            planet_evidence("Moon & Match-Time", a.sub_lord, "Ascendant sub lord", sig, rules)]
