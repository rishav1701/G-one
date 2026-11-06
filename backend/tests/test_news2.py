from decimal import Decimal

import pytest

from app.domain.news2 import Level, SpO2Scale, calculate_news2


def values(**overrides):
    result = {
        "respiration_rate": 12, "spo2": 97, "supplemental_o2": False,
        "systolic_bp": 120, "pulse": 70, "consciousness": "ALERT",
        "temperature": Decimal("37.0"),
    }
    result.update(overrides)
    return result


@pytest.mark.parametrize("value,expected", [(8, 3), (9, 1), (11, 1), (12, 0), (20, 0), (21, 2), (24, 2), (25, 3)])
def test_respiration_boundaries(value, expected):
    assert calculate_news2(values(respiration_rate=value)).scores["respiration_rate"] == expected


@pytest.mark.parametrize("value,expected", [(91, 3), (92, 2), (93, 2), (94, 1), (95, 1), (96, 0)])
def test_scale_one_boundaries(value, expected):
    assert calculate_news2(values(spo2=value), spo2_scale=SpO2Scale.SCALE_1).scores["spo2"] == expected


@pytest.mark.parametrize("value,oxygen,expected", [
    (83, False, 3), (84, False, 2), (85, False, 2), (86, False, 1),
    (87, False, 1), (88, False, 0), (92, False, 0), (93, False, 0),
    (93, True, 1), (94, True, 1), (95, True, 2), (96, True, 2), (97, True, 3),
])
def test_scale_two_boundaries(value, oxygen, expected):
    assert calculate_news2(values(spo2=value, supplemental_o2=oxygen), spo2_scale=SpO2Scale.SCALE_2).scores["spo2"] == expected


@pytest.mark.parametrize("value,expected", [(90, 3), (91, 2), (100, 2), (101, 1), (110, 1), (111, 0), (219, 0), (220, 3)])
def test_systolic_boundaries(value, expected):
    assert calculate_news2(values(systolic_bp=value)).scores["systolic_bp"] == expected


@pytest.mark.parametrize("value,expected", [(40, 3), (41, 1), (50, 1), (51, 0), (90, 0), (91, 1), (110, 1), (111, 2), (130, 2), (131, 3)])
def test_pulse_boundaries(value, expected):
    assert calculate_news2(values(pulse=value)).scores["pulse"] == expected


@pytest.mark.parametrize("value,expected", [("ALERT", 0), ("NEW_CONFUSION", 3), ("VOICE", 3), ("PAIN", 3), ("UNRESPONSIVE", 3)])
def test_consciousness_values(value, expected):
    assert calculate_news2(values(consciousness=value)).scores["consciousness"] == expected


@pytest.mark.parametrize("value,expected", [(Decimal("35.0"), 3), (Decimal("35.1"), 1), (Decimal("36.0"), 1), (Decimal("36.1"), 0), (Decimal("38.0"), 0), (Decimal("38.1"), 1), (Decimal("39.0"), 1), (Decimal("39.1"), 2)])
def test_temperature_boundaries(value, expected):
    assert calculate_news2(values(temperature=value)).scores["temperature"] == expected


def test_level_precedence_missing_data_and_oxygen():
    complete = calculate_news2(values())
    assert (complete.total, complete.level, complete.completeness) == (0, Level.LOW, 7)
    assert calculate_news2(values(respiration_rate=8)).level is Level.LOW_MEDIUM
    medium_values = values(respiration_rate=21, pulse=111, supplemental_o2=True)
    assert calculate_news2(medium_values).level is Level.MEDIUM
    assert calculate_news2(values(respiration_rate=8, supplemental_o2=True, pulse=131)).level is Level.HIGH
    incomplete = values(respiration_rate=21, spo2=None, supplemental_o2=None, systolic_bp=None, pulse=None, consciousness=None, temperature=None)
    assert calculate_news2(incomplete).level is Level.INCOMPLETE
    assert calculate_news2(values(respiration_rate=None, spo2=None, supplemental_o2=None, systolic_bp=None, pulse=None, consciousness=None, temperature=None)).level is Level.INCOMPLETE
    assert calculate_news2(values(respiration_rate=None, spo2=None, supplemental_o2=None, systolic_bp=None, pulse=None, consciousness=None, temperature=None), no_data=True).level is Level.NO_DATA
    assert calculate_news2(values(), stale=True).level is Level.STALE
    assert calculate_news2(values(respiration_rate=8, supplemental_o2=True)).total == 5


def test_invalid_inputs_are_rejected():
    with pytest.raises(ValueError, match="SpO2 scale"):
        calculate_news2(values(), spo2_scale=3)
    with pytest.raises(ValueError, match="supplemental_o2"):
        calculate_news2(values(supplemental_o2=None))
    with pytest.raises(ValueError, match="consciousness"):
        calculate_news2(values(consciousness="UNKNOWN"))
    with pytest.raises(ValueError, match="Unsupported NEWS2 parameter"):
        calculate_news2(values(unexpected=1))
    with pytest.raises(ValueError, match="stale and have no data"):
        calculate_news2(values(), stale=True, no_data=True)
    with pytest.raises(ValueError, match="stale and have no data"):
        calculate_news2(values(), stale=True, no_data=True)
