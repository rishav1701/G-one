"""NEWS2 scoring from the project-supplied RCP 2017 reference bands."""

from dataclasses import asdict, dataclass
from decimal import Decimal
from enum import Enum
from typing import Mapping


class Level(str, Enum):
    LOW = "LOW"
    LOW_MEDIUM = "LOW_MEDIUM"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    INCOMPLETE = "INCOMPLETE"
    STALE = "STALE"
    NO_DATA = "NO_DATA"


class SpO2Scale(int, Enum):
    SCALE_1 = 1
    SCALE_2 = 2


PARAMETERS = (
    "respiration_rate", "spo2", "supplemental_o2", "systolic_bp",
    "pulse", "consciousness", "temperature",
)


@dataclass(frozen=True)
class Assessment:
    scoring_version: str
    scores: dict[str, int]
    completeness: int
    total: int
    level: Level
    partial: bool
    lower_bound: bool

    def explanation(self) -> dict[str, object]:
        return asdict(self) | {"level": self.level.value}


def _score_rr(value: int) -> int:
    if value <= 8: return 3
    if value <= 11: return 1
    if value <= 20: return 0
    if value <= 24: return 2
    return 3


def _score_spo2(value: int, scale: SpO2Scale, oxygen: bool) -> int:
    if scale is SpO2Scale.SCALE_1:
        if value <= 91: return 3
        if value <= 93: return 2
        if value <= 95: return 1
        return 0
    if value <= 83: return 3
    if value <= 85: return 2
    if value <= 87: return 1
    if value <= 92: return 0
    if not oxygen: return 0
    if value <= 94: return 1
    if value <= 96: return 2
    return 3


def _score_sbp(value: int) -> int:
    if value <= 90: return 3
    if value <= 100: return 2
    if value <= 110: return 1
    if value <= 219: return 0
    return 3


def _score_pulse(value: int) -> int:
    if value <= 40: return 3
    if value <= 50: return 1
    if value <= 90: return 0
    if value <= 110: return 1
    if value <= 130: return 2
    return 3


def _score_consciousness(value: str) -> int:
    if value == "ALERT": return 0
    if value in {"NEW_CONFUSION", "VOICE", "PAIN", "UNRESPONSIVE"}: return 3
    raise ValueError("Unsupported consciousness value")


def _score_temperature(value: Decimal | float | int) -> int:
    temperature = Decimal(str(value))
    if temperature <= Decimal("35.0"): return 3
    if temperature <= Decimal("36.0"): return 1
    if temperature <= Decimal("38.0"): return 0
    if temperature <= Decimal("39.0"): return 1
    return 2


def _level(total: int, has_three: bool, missing: bool) -> Level:
    if total >= 7: return Level.HIGH
    if total >= 5: return Level.MEDIUM
    if has_three: return Level.LOW_MEDIUM
    if missing: return Level.INCOMPLETE
    return Level.LOW


def calculate_news2(
    values: Mapping[str, object | None],
    *,
    spo2_scale: SpO2Scale = SpO2Scale.SCALE_1,
    scoring_version: str = "NEWS2-RCP-2017-v1",
    stale: bool = False,
    no_data: bool = False,
) -> Assessment:
    """Calculate a deterministic complete or partial assessment.

    Missing observations are omitted from scoring; they are never imputed as zero.
    ``supplemental_o2`` is a known boolean value when present.
    """
    if stale and no_data:
        raise ValueError("An assessment cannot be stale and have no data")
    if not isinstance(spo2_scale, SpO2Scale):
        raise ValueError("Unsupported SpO2 scale")
    unknown = set(values) - set(PARAMETERS)
    if unknown:
        raise ValueError("Unsupported NEWS2 parameter")
    present = {key: values.get(key) for key in PARAMETERS}
    oxygen = present["supplemental_o2"]
    scores: dict[str, int] = {}
    if present["respiration_rate"] is not None:
        scores["respiration_rate"] = _score_rr(int(present["respiration_rate"]))
    if present["spo2"] is not None:
        if oxygen is None:
            raise ValueError("supplemental_o2 is required when SpO2 is present")
        scores["spo2"] = _score_spo2(int(present["spo2"]), spo2_scale, bool(oxygen))
    if oxygen is not None:
        scores["supplemental_o2"] = 2 if bool(oxygen) else 0
    if present["systolic_bp"] is not None:
        scores["systolic_bp"] = _score_sbp(int(present["systolic_bp"]))
    if present["pulse"] is not None:
        scores["pulse"] = _score_pulse(int(present["pulse"]))
    if present["consciousness"] is not None:
        scores["consciousness"] = _score_consciousness(str(present["consciousness"]))
    if present["temperature"] is not None:
        scores["temperature"] = _score_temperature(present["temperature"])
    total = sum(scores.values())
    completeness = len(scores)
    missing = completeness < len(PARAMETERS)
    level = Level.STALE if stale else Level.NO_DATA if no_data else _level(total, any(score == 3 for score in scores.values()), missing)
    return Assessment(
        scoring_version=scoring_version,
        scores=scores,
        completeness=completeness,
        total=total,
        level=level,
        partial=missing,
        lower_bound=missing,
    )
