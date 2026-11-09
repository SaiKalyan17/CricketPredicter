"""Core KP maths: signs, nakshatras, Vimshottari star/sub/sub-sub, 249 horary table."""
from dataclasses import dataclass

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
         "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars",
              "Jupiter", "Saturn", "Saturn", "Jupiter"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu",
              "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
              "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
              "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
              "Uttara Bhadrapada", "Revati"]
DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18,
               "Jupiter": 16, "Saturn": 19, "Mercury": 17}
NAK_LEN = 360.0 / 27
EPS = 1e-9


@dataclass(frozen=True)
class KPInfo:
    longitude: float
    sign: str
    sign_lord: str
    nakshatra: str
    star_lord: str
    sub_lord: str
    sub_sub_lord: str
    degree_in_sign: float


def _split(offset: float, length: float, first_lord: str):
    """Proportional Vimshottari split of a segment. Returns (lord, offset_in_sub, sub_length)."""
    start = DASHA_ORDER.index(first_lord)
    pos = 0.0
    for i in range(9):
        lord = DASHA_ORDER[(start + i) % 9]
        ln = length * DASHA_YEARS[lord] / 120.0
        if offset < pos + ln - EPS or i == 8:
            return lord, max(offset - pos, 0.0), ln
        pos += ln
    raise AssertionError("unreachable")


def kp_info(longitude: float) -> KPInfo:
    lon = longitude % 360.0
    ni = min(int(lon // NAK_LEN), 26)
    star = DASHA_ORDER[ni % 9]
    off = max(lon - ni * NAK_LEN, 0.0)
    sub, sub_off, sub_len = _split(off, NAK_LEN, star)
    subsub, _, _ = _split(sub_off, sub_len, sub)
    si = int(lon // 30) % 12
    return KPInfo(lon, SIGNS[si], SIGN_LORDS[si], NAKSHATRAS[ni], star, sub, subsub, lon - si * 30)


def build_horary_table() -> list:
    """249 KP horary divisions: 243 subs, split further at the 6 sign boundaries inside nakshatras."""
    rows = []
    for ni in range(27):
        cum = ni * NAK_LEN
        star = DASHA_ORDER[ni % 9]
        s = DASHA_ORDER.index(star)
        for j in range(9):
            lord = DASHA_ORDER[(s + j) % 9]
            ln = NAK_LEN * DASHA_YEARS[lord] / 120.0
            a, b = cum, cum + ln
            cuts = [a] + [k * 30.0 for k in range(1, 12) if a + EPS < k * 30.0 < b - EPS] + [b]
            for x, y in zip(cuts[:-1], cuts[1:]):
                rows.append({"start": x, "end": y, "star_lord": star, "sub_lord": lord,
                             "sign": SIGNS[int((x + EPS) // 30) % 12]})
            cum = b
    for n, r in enumerate(rows, 1):
        r["number"] = n
    return rows


HORARY_TABLE = build_horary_table()


def horary_number_longitude(number: int) -> float:
    """Ascendant longitude (sidereal) for horary number: start of the division (+tiny offset
    so the boundary resolves into the correct sub)."""
    if not 1 <= int(number) <= 249:
        raise ValueError("Horary number must be 1-249")
    return HORARY_TABLE[int(number) - 1]["start"] + 1e-7
