"""Synthetic station client that uses the exact same ingestion contract as a future device."""

from __future__ import annotations

import logging
import math
import os
import random
import time
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s simulator: %(message)s")
logger = logging.getLogger("simulator")

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1").rstrip("/")
INTERVAL_SECONDS = int(os.getenv("SIMULATOR_INTERVAL_SECONDS", "300"))
SENSORS = (
    ("KRG-001", "demo-krg-001-token", 22.0),
    ("KRG-002", "demo-krg-002-token", 40.0),
    ("KRG-003", "demo-krg-003-token", 27.0),
    ("KRG-004", "demo-krg-004-token", 18.0),
)


def make_payload(code: str, baseline: float, sequence: int) -> dict[str, object]:
    rng = random.Random(f"{code}-{sequence}")
    pollution = max(3, baseline + math.sin(sequence / 3) * 6 + rng.uniform(-4, 4))
    # Rare synthetic event, labelled in every request as simulator data.
    if code == "KRG-002" and sequence % 13 in (10, 11):
        pollution += 36
    return {
        "station_code": code,
        "measured_at": datetime.now(timezone.utc).isoformat(),
        "pm25": round(pollution, 1),
        "pm10": round(pollution * rng.uniform(1.45, 1.9), 1),
        "co": round(max(0.1, 0.8 + pollution / 45 + rng.uniform(-0.2, 0.2)), 2),
        "no2": round(max(3, 38 + pollution * 1.05 + rng.uniform(-8, 8)), 1),
        "so2": round(max(2, 14 + pollution * 0.28 + rng.uniform(-4, 4)), 1),
        "o3": round(max(3, 48 - pollution * 0.23 + rng.uniform(-5, 5)), 1),
        "temperature": round(-1 + rng.uniform(-2, 2), 1),
        "humidity": round(64 + rng.uniform(-9, 9), 1),
        "source": "simulator",
    }


def run() -> None:
    logger.info("Starting synthetic feed to %s every %ss", API_BASE_URL, INTERVAL_SECONDS)
    sequence = 0
    while True:
        for code, token, baseline in SENSORS:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/ingest/measurements",
                    json=make_payload(code, baseline, sequence),
                    headers={"X-API-Key": token},
                    timeout=10,
                )
                response.raise_for_status()
                logger.info("%s → accepted", code)
            except requests.RequestException as error:
                logger.warning("%s → retry next cycle (%s)", code, error)
        sequence += 1
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    run()

