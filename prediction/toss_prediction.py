"""Toss prediction from the 3rd-house cuspal sub-lord (CSL), per the KP toss rules.

Rules (queried team = Team A, the querent; Team B is the opposite):
  * WIN  : 3rd CSL signifies 1, 2, 3, 6, 10 or 11 AND is connected to 3, 6, 10 or 11.
  * LOSE : 3rd CSL signifies 4, 5, 7, 8, 9 or 12.
If the CSL signifies houses from both groups, the larger group decides; a WIN additionally needs a
3/6/10/11 connection, otherwise it is a LOSS. A tie in group size is a LOSS (win needs clear support).
The toss always yields a winner (no "uncertain" result).
"""
TOSS_WIN_HOUSES = frozenset({1, 2, 3, 6, 10, 11})
TOSS_CONNECT_HOUSES = frozenset({3, 6, 10, 11})
TOSS_LOSE_HOUSES = frozenset({4, 5, 7, 8, 9, 12})


def evaluate_toss_houses(houses) -> dict:
    """Pure rule check on the houses signified by the 3rd CSL, for the queried team."""
    hs = set(houses)
    win, lose = hs & TOSS_WIN_HOUSES, hs & TOSS_LOSE_HOUSES
    connected = bool(hs & TOSS_CONNECT_HOUSES)
    queried_wins = connected and len(win) > len(lose)
    return {"houses": sorted(hs), "win_houses": sorted(win), "lose_houses": sorted(lose),
            "connected": connected, "queried_wins": queried_wins}


def predict_toss(chart, sig: dict, names) -> dict:
    csl = chart.cusp_info[2].sub_lord            # cusp 3
    houses = sorted(sig.get(csl, {}))
    r = evaluate_toss_houses(houses)
    winner = names[0] if r["queried_wins"] else names[1]
    why = (f"3rd-cusp sub-lord {csl} signifies houses {r['houses'] or 'none'}: "
           f"win-group {r['win_houses']}, lose-group {r['lose_houses']}, "
           f"3/6/10/11 connection {'yes' if r['connected'] else 'no'}. "
           f"{names[0]} (queried team) {'wins' if r['queried_wins'] else 'loses'} the toss.")
    return {"csl": csl, "winner": winner, "queried_wins": r["queried_wins"], "detail": r,
            "chart": chart.label, "note": why}


def predict_batting_first(toss_winner: str, names, inn1_favoured: str) -> dict:
    """Heuristic (not part of the supplied rules): the toss winner bats first when it is the side
    favoured in the first-innings (match-start) analysis, otherwise it chooses to field."""
    if inn1_favoured not in names:
        return {"decision": "bat", "batting_first": toss_winner, "basis": "default (first-innings support balanced/unavailable): toss winner bats"}
    bats = inn1_favoured == toss_winner
    other = names[1] if toss_winner == names[0] else names[0]
    return {"decision": "bat" if bats else "field",
            "batting_first": toss_winner if bats else other,
            "basis": f"{inn1_favoured} favoured in first innings; toss winner {toss_winner} "
                     f"{'bats' if bats else 'fields'}"}
