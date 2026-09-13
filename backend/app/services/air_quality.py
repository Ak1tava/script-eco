from __future__ import annotations

from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class AqiResult:
    value: int
    category: str


# US EPA AQI tables are used only as a transparent, familiar index for the demo.
# Individual pollutant thresholds below are MVP operational thresholds, editable in one place.
PM25_BREAKPOINTS = (
    (0.0, 12.0, 0, 50),
    (12.1, 35.4, 51, 100),
    (35.5, 55.4, 101, 150),
    (55.5, 150.4, 151, 200),
    (150.5, 250.4, 201, 300),
    (250.5, 500.4, 301, 500),
)
PM10_BREAKPOINTS = (
    (0, 54, 0, 50),
    (55, 154, 51, 100),
    (155, 254, 101, 150),
    (255, 354, 151, 200),
    (355, 424, 201, 300),
    (425, 604, 301, 500),
)

AQI_CATEGORIES = (
    (50, "Хорошее"),
    (100, "Умеренное"),
    (150, "Нездоровое для чувствительных групп"),
    (200, "Нездоровое"),
    (300, "Очень нездоровое"),
    (500, "Опасное"),
)


def _sub_index(value: float, breakpoints: tuple[tuple[float, float, int, int], ...]) -> int:
    for concentration_low, concentration_high, index_low, index_high in breakpoints:
        if value <= concentration_high:
            return ceil(
                (index_high - index_low) / (concentration_high - concentration_low)
                * (value - concentration_low)
                + index_low
            )
    return 500


def category_for_aqi(aqi: int) -> str:
    for upper_bound, category in AQI_CATEGORIES:
        if aqi <= upper_bound:
            return category
    return "Опасное"


def calculate_aqi(pm25: float, pm10: float) -> AqiResult:
    """Calculate the maximum particulate AQI for one measurement."""
    aqi = max(_sub_index(pm25, PM25_BREAKPOINTS), _sub_index(pm10, PM10_BREAKPOINTS))
    return AqiResult(value=min(aqi, 500), category=category_for_aqi(aqi))


@dataclass(frozen=True)
class Threshold:
    value: float
    unit: str
    label: str


THRESHOLDS: dict[str, Threshold] = {
    "pm25": Threshold(55.0, "µg/m³", "PM2.5"),
    "pm10": Threshold(150.0, "µg/m³", "PM10"),
    "no2": Threshold(200.0, "µg/m³", "NO₂"),
    "so2": Threshold(350.0, "µg/m³", "SO₂"),
    "o3": Threshold(180.0, "µg/m³", "O₃"),
    "co": Threshold(10.0, "mg/m³", "CO"),
}


def severity_for(metric: str, value: float) -> str:
    threshold = THRESHOLDS[metric].value
    if value >= threshold * 2:
        return "critical"
    if value >= threshold * 1.4:
        return "high"
    return "warning"

