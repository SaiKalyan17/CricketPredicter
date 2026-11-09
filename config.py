"""Configurable assumptions. KP practitioners differ; every rule here can be changed."""
from dataclasses import dataclass, field

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

AYANAMSAS = {  # label -> name (computed natively; KP Old/VP291 is not supported without pyswisseph)
    "KP New (Krishnamurti)": "SIDM_KRISHNAMURTI",
    "Lahiri": "SIDM_LAHIRI",
}
HOUSE_SYSTEMS = {"Placidus (KP standard)": "P", "Equal": "E", "Whole Sign": "W"}
NODE_TYPES = {"Mean Node": "mean", "True Node": "true"}


@dataclass
class HouseRules:
    own_a: int = 1            # house representing Team A
    own_b: int = 7            # house representing Team B
    shared_positive: tuple = (5, 6, 10, 11)
    shared_negative: tuple = (8, 12)

    def positive(self, team: str) -> set:
        own = self.own_a if team == "A" else self.own_b
        return {own, *self.shared_positive}

    def negative(self, team: str) -> set:
        opp = self.own_b if team == "A" else self.own_a
        return {opp, *self.shared_negative}


# Significator hierarchy weights (strongest level wins per planet/house pair).
SIGNIFICATOR_WEIGHTS = {"L1_star_of_occupant": 1.0, "L2_occupant": 0.8,
                        "L3_star_of_owner": 0.6, "L4_owner": 0.4}

DEFAULT_WEIGHTS = {
    "KP House Significators": 0.25,
    "Horary CSL": 0.20,
    "Ruling Planets": 0.20,
    "Transits": 0.15,
    "Dasha": 0.10,
    "Moon & Match-Time": 0.10,
}
CSL_CUSP_WEIGHTS = {1: 1.5, 7: 1.5, 6: 1.0, 10: 1.0, 11: 1.0}
RP_REPEAT_MULTIPLIER = 1.5   # planet present in both match-time and horary-time RP
MIN_COVERAGE = 0.40          # minimum share of total weight with data, else UNCERTAIN
DECISION_MARGIN = 5.0        # percentage points away from 50 required for WIN/LOSS
YEAR_DAYS = 365.25           # Vimshottari year length
