from datetime import datetime
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from iqair_karaganda import StationLink, discover_stations, parse_station_snapshot


CITY_PAGE = """
<a href="/air-quality/kazakhstan/karaganda/karaganda/mukanova">Mukanova</a>
<a href="/air-quality/kazakhstan/karaganda/karaganda/likhacheva-4">Likhacheva 4</a>
<a href="/air-quality/kazakhstan/karaganda">Karaganda region</a>
"""
STATION_PAGE = """
<h1>Air quality near Mukanova, Karaganda</h1>
<p>Air quality index (AQI+) and PM2.5 air pollution near Mukanova • 15:00, Sep 08 Local time</p>
<div>17</div><div>US AQI+</div><div>Good</div>
<div>Main pollutant: PM2.5 3 µg/m³</div>
"""


def test_discover_all_station_links() -> None:
    stations = discover_stations(CITY_PAGE, "https://www.iqair.com/air-quality/kazakhstan/karaganda/karaganda")

    assert [station.name for station in stations] == ["Mukanova", "Likhacheva 4"]
    assert stations[1].url.endswith("/likhacheva-4")


def test_parse_station_snapshot() -> None:
    snapshot = parse_station_snapshot(
        STATION_PAGE,
        StationLink("Mukanova", "https://example.test/mukanova"),
        datetime(2026, 9, 10, 5, 0, tzinfo=ZoneInfo("Asia/Almaty")),
    )

    assert snapshot.station_name == "Mukanova"
    assert snapshot.aqi_us == 17
    assert snapshot.category == "Good"
    assert snapshot.main_pollutant == "PM2.5"
    assert snapshot.pollutant_concentration_ug_m3 == 3
    assert snapshot.taken_at_karaganda == "2026-09-10T05:00:00+05:00"
