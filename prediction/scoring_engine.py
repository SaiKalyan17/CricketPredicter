"""Transparent, configurable scoring. Same maths for both teams; missing data is excluded and
lowers coverage/confidence rather than being filled in."""
from config import DECISION_MARGIN, DEFAULT_WEIGHTS, MIN_COVERAGE
from prediction.team_analysis import dedupe, team_ratio


def score_category(name: str, evidence: list, unavailable_reason: str = "") -> dict:
    evs = dedupe(evidence)
    if not evs:
        return {"name": name, "available": False, "A": None, "B": None, "evidence": [],
                "reason": unavailable_reason or "No qualifying evidence"}
    ra, pa, na = team_ratio(evs, "A")
    rb, pb, nb = team_ratio(evs, "B")
    return {"name": name, "available": True, "A": ra, "B": rb, "evidence": evs, "reason": "",
            "A_pos": pa, "A_neg": na, "B_pos": pb, "B_neg": nb}


def normalize(sa: float, sb: float):
    """Return (pA, pB) percentages, or None if there is no evidence at all."""
    t = sa + sb
    if t <= 0:
        return None
    return 100 * sa / t, 100 * sb / t


def combine(categories: list, weights: dict = None, min_coverage=MIN_COVERAGE,
            margin=DECISION_MARGIN) -> dict:
    weights = weights or DEFAULT_WEIGHTS
    total_w = sum(weights.values())
    avail = [c for c in categories if c["available"] and weights.get(c["name"], 0) > 0]
    avail_w = sum(weights[c["name"]] for c in avail)
    coverage = avail_w / total_w if total_w else 0.0
    out = {"coverage": coverage, "categories": categories, "weights": weights,
           "contributions": [], "pA": None, "pB": None}
    if not avail:
        out.update(verdict="UNCERTAIN", confidence="None",
                   explanation="No analysis had data, so no winning percentage can be computed.")
        return out
    sa = sb = 0.0
    for c in avail:
        w = weights[c["name"]] / avail_w
        a, b = c["A"] or 0.0, c["B"] or 0.0
        sa += w * a
        sb += w * b
        out["contributions"].append({"category": c["name"], "effective_weight": w,
                                     "A_ratio": c["A"], "B_ratio": c["B"],
                                     "A_points": w * a, "B_points": w * b})
    probs = normalize(sa, sb)
    if probs is None:
        out.update(verdict="UNCERTAIN", confidence="None", explanation="No favourable evidence for either team.")
        return out
    pa, pb = probs
    out.update(pA=pa, pB=pb)
    diff = abs(pa - 50)
    strength = min(1.0, diff / 25) * coverage
    out["confidence"] = "High" if strength > 0.6 else "Medium" if strength > 0.3 else "Low"
    # Always pick the team with the higher winning percentage (exact tie -> Team A).
    out["verdict"] = "WIN" if pa >= pb else "LOSS"      # relative to Team A
    out["explanation"] = "Team A has stronger support." if pa >= pb else "Team B has stronger support."
    return out
