# KP Astrology Cricket Match Prediction (Streamlit)

Compares two teams with identical rules using KP significators, horary cusp sub lords, ruling planets,
transits, Vimshottari periods and match-time Moon/ascendant. Output is a **model-derived support score**,
not a validated probability, and never a guaranteed result.

## Setup
```
python -m venv .venv && .venv\Scripts\activate     # Python 3.11-3.13 recommended
pip install -r requirements.txt
streamlit run app.py
pytest
```
No pyswisseph needed. Planets come from **PyEphem** (pure wheels, incl. Python 3.14); ayanamsa, lunar nodes,
sidereal time and Placidus/Equal/Whole-Sign cusps are computed natively. Manual planet/cusp entry is always available.

### Native-engine accuracy / limits
- Planets: ~arc-second (apparent geocentric longitude of date). Moon checked against Meeus example 47.a.
- **Mean node** is exact to Meeus; **True node** uses Meeus' main corrections only (~0.1-0.3 deg). Mean is the default.
- Ayanamsa: KP New and Lahiri only (J1900 epoch value + general precession). KP Old (VP291), Koch and Porphyry
  are not supported and raise an explicit error.
- Placidus is undefined at circumpolar latitudes; use Equal/Whole Sign or manual cusps there.

## Layout
`astrology/` KP maths, positions, cusps, significators, RP, horary, transits, dasha ·
`prediction/` evidence, scoring, orchestration · `utils/` validation, time, charts · `tests/`.

## Method (all configurable in `config.py` / sidebar)
- **Star/sub/sub-sub**: Vimshottari proportional split of 13°20' nakshatras. Horary 1-249 table built from
  243 subs plus splits at sign boundaries; ascendant = start of the division.
- **Horary chart**: planets at question time; cusps computed for the time at which the ascendant equals the
  horary-number longitude (same place).
- **Significators**: star of occupant (1.0) > occupant (0.8) > star of owner (0.6) > owner (0.4).
  House owner = lord of the cusp sign (intercepted signs ignored). Rahu/Ketu are not treated as agents of sign lords.
- **Houses**: Team A positive 1,5,6,10,11 / negative 7,8,12; Team B positive 7,5,6,10,11 / negative 1,8,12.
  Swapping teams and `own_a/own_b` yields mirrored scores (tested).
- **Category score** per team = weighted positives / (positives + negatives); each planet counted once per category.
  Final: weights renormalised over categories with data; `pA = SA/(SA+SB)`.
- **Verdict**: WIN = Team A favoured, LOSS = Team B favoured, UNCERTAIN if coverage < 40% or margin < 5 pts.
- **Day lord** uses computed sunrise (PyEphem), otherwise civil midnight (flagged).
- **Dasha**: reference = horary-chart Moon at question time (or manual MD/AD/AL). No birth data is assumed.

## Limitations
Toss prediction is experimental; second innings needs a start time; batting order is never assumed;
PDF export is not implemented (CSV and JSON downloads are). KP event-house rules vary between practitioners.
