#!/usr/bin/env python3
"""Collect one IQAir snapshot from every public station listed for Karaganda.

The collector makes one request to the city page to discover its current station
links, then one request per discovered station. It does not guess station URLs,
retry aggressively, or try to bypass rate limits. If a particular station page
is unavailable, the other stations are still saved and the failure is logged.
"""

from __future__ import annotations

import argparse
import csv
import html
import logging
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

import requests


DEFAULT_URL = "https://www.iqair.com/air-quality/kazakhstan/karaganda/karaganda"
KARAGANDA_TZ = ZoneInfo("Asia/Almaty")
USER_AGENT = "EcoWatchKaraganda/1.1 (+local educational air-quality monitoring)"


class PageExtractor(HTMLParser):
    """Extract normalized visible text and links from server-rendered HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._link_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._link_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href:
            self.links.append((self._href, " ".join(self._link_parts).strip()))
            self._href = None
            self._link_parts = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)
        if self._href is not None:
            self._link_parts.append(data)

    @property
    def text(self) -> str:
        return re.sub(r"\s+", " ", html.unescape(" ".join(self.parts))).strip()


@dataclass(frozen=True)
class StationLink:
    name: str
    url: str


@dataclass(frozen=True)
class StationSnapshot:
    taken_at_karaganda: str
    station_name: str
    source_updated_local: str
    aqi_us: int
    category: str
    main_pollutant: str
    pollutant_concentration_ug_m3: float
    source_url: str


def _match(pattern: str, text: str, label: str) -> re.Match[str]:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"IQAir page format changed: cannot find {label}")
    return match


def discover_stations(city_html: str, city_url: str) -> list[StationLink]:
    """Return only links to stations within the requested Karaganda city page."""
    parser = PageExtractor()
    parser.feed(city_html)
    city_path = urlparse(city_url).path.rstrip("/")
    station_prefix = f"{city_path}/"
    seen: set[str] = set()
    stations: list[StationLink] = []

    for href, anchor_text in parser.links:
        station_url = urljoin(city_url, href).split("?", 1)[0].rstrip("/")
        station_path = urlparse(station_url).path
        if not station_path.startswith(station_prefix) or station_url in seen:
            continue
        name = re.sub(r"\s+", " ", html.unescape(anchor_text)).strip()
        if not name:
            continue
        seen.add(station_url)
        stations.append(StationLink(name=name, url=station_url))

    if not stations:
        raise ValueError("IQAir page format changed: cannot find public station links")
    return stations


def parse_station_snapshot(
    page_html: str,
    station: StationLink,
    captured_at: datetime | None = None,
) -> StationSnapshot:
    """Parse the current station value from an IQAir station page."""
    parser = PageExtractor()
    parser.feed(page_html)
    text = parser.text

    # The current station value is immediately before the "US AQI" label;
    # forecast values have their time after the AQI and do not match this form.
    aqi_match = _match(r"\b(\d{1,3})\s+US\s+AQI(?:\+)?\b", text, "US AQI")
    pollutant_match = _match(
        r"Main\s+pollutant:\s*(PM2\.5|PM10|O[₃3]|NO[₂2]|SO[₂2]|CO)\s*(\d+(?:[.,]\d+)?)\s*[µu]g/m[³3]",
        text,
        "main pollutant concentration",
    )
    updated_match = _match(
        r"PM2\.5\s+air\s+pollution.*?[•·]\s*(.*?)\s+Local\s+time",
        text,
        "IQAir update time",
    )
    category_match = re.search(
        r"\b\d{1,3}\s+US\s+AQI(?:\+)?\s+(Good|Moderate|Unhealthy(?:\s+for\s+Sensitive\s+Groups)?|Very\s+Unhealthy|Hazardous)\b",
        text,
        flags=re.IGNORECASE,
    )
    captured_at = captured_at or datetime.now(KARAGANDA_TZ)

    return StationSnapshot(
        taken_at_karaganda=captured_at.astimezone(KARAGANDA_TZ).isoformat(timespec="seconds"),
        station_name=station.name,
        source_updated_local=updated_match.group(1).strip(),
        aqi_us=int(aqi_match.group(1)),
        category=category_match.group(1) if category_match else "",
        main_pollutant=pollutant_match.group(1),
        pollutant_concentration_ug_m3=float(pollutant_match.group(2).replace(",", ".")),
        source_url=station.url,
    )


def fetch_html(url: str) -> str:
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
        timeout=30,
    )
    response.raise_for_status()
    return response.text


def append_snapshots(snapshots: list[StationSnapshot], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(StationSnapshot.__dataclass_fields__)
    write_header = not output.exists() or output.stat().st_size == 0
    if not write_header:
        with output.open(encoding="utf-8", newline="") as csv_file:
            if next(csv.reader(csv_file), []) != fieldnames:
                raise ValueError(f"{output} has another CSV format; choose a new --output file")
    with output.open("a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerows(asdict(snapshot) for snapshot in snapshots)


def main() -> int:
    arg_parser = argparse.ArgumentParser(description=__doc__)
    arg_parser.add_argument("--url", default=DEFAULT_URL, help="IQAir city page URL")
    arg_parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "iqair_karaganda_stations.csv",
        help="CSV file to append (default: backend/data/iqair_karaganda_stations.csv)",
    )
    arg_parser.add_argument(
        "--delay-seconds",
        type=float,
        default=1.0,
        help="pause between station page requests; default: 1 second",
    )
    args = arg_parser.parse_args()
    if args.delay_seconds < 0:
        arg_parser.error("--delay-seconds must be zero or greater")

    try:
        stations = discover_stations(fetch_html(args.url), args.url)
    except (requests.RequestException, ValueError) as error:
        logging.error("IQAir station discovery failed: %s", error)
        return 1

    snapshots: list[StationSnapshot] = []
    for index, station in enumerate(stations):
        if index:
            time.sleep(args.delay_seconds)
        try:
            snapshots.append(parse_station_snapshot(fetch_html(station.url), station))
        except (requests.RequestException, ValueError) as error:
            logging.warning("Skipped station %s (%s): %s", station.name, station.url, error)

    if not snapshots:
        logging.error("No IQAir station snapshots were saved")
        return 1
    try:
        append_snapshots(snapshots, args.output)
    except ValueError as error:
        logging.error("IQAir collection failed: %s", error)
        return 1

    logging.info("Saved %s of %s discovered IQAir stations -> %s", len(snapshots), len(stations), args.output)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    sys.exit(main())
