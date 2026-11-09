"""KP significators. Hierarchy: star of occupant > occupant > star of owner > owner."""
from astrology.house_cusps import Chart
from config import SIGNIFICATOR_WEIGHTS as W


def house_owner(chart: Chart, house: int) -> str:
    """Owner = lord of the sign on the cusp (simplification: intercepted signs ignored)."""
    return chart.cusp_info[house - 1].sign_lord


def planet_significations(chart: Chart, weights: dict = W) -> dict:
    """{planet: {house: (weight, level)}}, strongest level kept per planet/house pair."""
    occupants = {h: [] for h in range(1, 13)}
    for p, pos in chart.planets.items():
        occupants[chart.house_of(pos.longitude)].append(p)
    res = {p: {} for p in chart.planets}
    for p, pos in chart.planets.items():
        star = pos.info.star_lord
        for h in range(1, 13):
            owner = house_owner(chart, h)
            cands = []
            if star in occupants[h]:
                cands.append("L1_star_of_occupant")
            if p in occupants[h]:
                cands.append("L2_occupant")
            if star == owner:
                cands.append("L3_star_of_owner")
            if p == owner:
                cands.append("L4_owner")
            if cands:
                lvl = max(cands, key=lambda c: weights[c])
                res[p][h] = (weights[lvl], lvl)
    return res


def houses_of_planet(sig: dict, planet: str) -> dict:
    return {h: w for h, (w, _) in sig.get(planet, {}).items()}
