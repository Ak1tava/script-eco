from datetime import datetime, timedelta, timezone
import math
import random

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AirMeasurement, Station
from app.services.air_quality import calculate_aqi
from app.services.alerts import evaluate_measurement


STATIONS = (
    {
        "code": "KRG-001",
        "name": "Станция «Юго-Восток»",
        "district": "Юго-Восток",
        "address": "проспект Республики, 40",
        "latitude": 49.8067,
        "longitude": 73.1238,
        "ingest_token": "demo-krg-001-token",
    },
    {
        "code": "KRG-002",
        "name": "Станция «Майкудук»",
        "district": "Майкудук",
        "address": "улица Магнитогорская, 18",
        "latitude": 49.8806,
        "longitude": 73.0950,
        "ingest_token": "demo-krg-002-token",
    },
    {
        "code": "KRG-003",
        "name": "Станция «Пришахтинск»",
        "district": "Пришахтинск",
        "address": "улица Металлистов, 12",
        "latitude": 49.8382,
        "longitude": 73.0705,
        "ingest_token": "demo-krg-003-token",
    },
    {
        "code": "KRG-004",
        "name": "Станция «Новый город»",
        "district": "Новый город",
        "address": "бульвар Мира, 15",
        "latitude": 49.8045,
        "longitude": 73.0918,
        "ingest_token": "demo-krg-004-token",
    },
)


def _demo_payload(station_index: int, point_index: int, total: int, rng: random.Random) -> dict[str, float]:
    """Plausible-looking values only; they do not represent measurements in Karaganda."""
    wave = math.sin(point_index / 7 + station_index)
    pm25_base = (20, 34, 25, 17)[station_index] + wave * 5 + rng.uniform(-3, 3)
    pm10_base = pm25_base * rng.uniform(1.45, 1.9)
    # One obvious current event makes the alert workflow demonstrable from first launch.
    if station_index == 1 and point_index >= total - 4:
        pm25_base += 52
        pm10_base += 84
    pm25 = round(max(2, pm25_base), 1)
    return {
        "pm25": pm25,
        "pm10": round(max(5, pm10_base), 1),
        "co": round(max(0.1, 1.1 + pm25 / 42 + rng.uniform(-0.25, 0.25)), 2),
        "no2": round(max(5, 38 + pm25 * 1.15 + rng.uniform(-9, 9)), 1),
        "so2": round(max(2, 16 + pm25 * 0.28 + rng.uniform(-4, 4)), 1),
        "o3": round(max(4, 42 - pm25 * 0.2 + rng.uniform(-5, 5)), 1),
        "temperature": round(-2 + wave * 1.8 + rng.uniform(-0.5, 0.5), 1),
        "humidity": round(63 + wave * 7 + rng.uniform(-3, 3), 1),
    }


def seed_database(db: Session) -> None:
    """Populate an explicitly labelled demo network and six hours of synthetic history."""
    if db.scalar(select(func.count()).select_from(Station)):
        return

    stations = [Station(**station) for station in STATIONS]
    db.add_all(stations)
    db.flush()

    rng = random.Random(20260908)
    sample_count = 72
    start = datetime.now(timezone.utc).replace(second=0, microsecond=0) - timedelta(minutes=(sample_count - 1) * 5)
    latest: list[tuple[Station, AirMeasurement]] = []
    for station_index, station in enumerate(stations):
        for point_index in range(sample_count):
            payload = _demo_payload(station_index, point_index, sample_count, rng)
            aqi = calculate_aqi(payload["pm25"], payload["pm10"])
            measurement = AirMeasurement(
                station_id=station.id,
                measured_at=start + timedelta(minutes=point_index * 5),
                aqi=aqi.value,
                aqi_category=aqi.category,
                source="demo_seed",
                **payload,
            )
            db.add(measurement)
            if point_index == sample_count - 1:
                latest.append((station, measurement))
    db.flush()
    for station, measurement in latest:
        evaluate_measurement(db, station, measurement)
    db.commit()

