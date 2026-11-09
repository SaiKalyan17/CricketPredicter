from datetime import datetime, timezone

from astrology.house_cusps import build_chart

SETTINGS = {"ayanamsa": "KP New (Krishnamurti)", "house_system": "Placidus (KP standard)", "node": "true"}
CUSPS = [i * 30.0 + 5 for i in range(12)]
PLANETS = {"Sun": 10.0, "Moon": 95.0, "Mars": 130.0, "Mercury": 200.0, "Jupiter": 250.0,
           "Venus": 280.0, "Saturn": 320.0, "Rahu": 45.0}
DT = datetime(2026, 3, 1, 14, 0, tzinfo=timezone.utc)


def manual_chart(planets=None, cusps=None, label="t"):
    return build_chart(label, DT, 19.0, 72.0, SETTINGS, planets or PLANETS, cusps or CUSPS)
