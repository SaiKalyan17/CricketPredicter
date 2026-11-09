"""Team-neutral evidence construction. Both teams are evaluated by identical rules."""
from config import HouseRules


def planet_evidence(category, planet, role, sig, rules: HouseRules, mult=1.0):
    """Evidence record for one planet from a significator table. None if planet signifies no
    positive/negative house for either team (nothing to count)."""
    houses = {h: w for h, (w, _) in sig.get(planet, {}).items()}
    ev = {"category": category, "planet": planet, "roles": [role], "houses": sorted(houses),
          "mult": mult}
    for team in ("A", "B"):
        pos = sum(w for h, w in houses.items() if h in rules.positive(team))
        neg = sum(w for h, w in houses.items() if h in rules.negative(team))
        ev[team] = {"pos": pos, "neg": neg}
    if not any(ev[t]["pos"] + ev[t]["neg"] for t in ("A", "B")):
        return None
    return ev


def dedupe(evidence: list) -> list:
    """One record per planet per category: keep the highest multiplier, merge roles."""
    out = {}
    for ev in evidence:
        if ev is None:
            continue
        cur = out.get(ev["planet"])
        if cur is None:
            out[ev["planet"]] = {**ev, "roles": list(ev["roles"])}
        else:
            cur["roles"] += [r for r in ev["roles"] if r not in cur["roles"]]
            cur["mult"] = max(cur["mult"], ev["mult"])
    return list(out.values())


def team_ratio(evidence: list, team: str):
    """Support ratio = weighted positives / weighted (positives + negatives)."""
    pos = sum(e["mult"] * e[team]["pos"] for e in evidence)
    neg = sum(e["mult"] * e[team]["neg"] for e in evidence)
    return (pos / (pos + neg) if pos + neg > 0 else None), pos, neg
