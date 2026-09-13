from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AirMeasurement, Alert, Notification, Station
from app.services.air_quality import THRESHOLDS, severity_for

logger = logging.getLogger(__name__)


class ConsoleNotificationChannel:
    """MVP delivery adapter. Replace with email/Telegram/SMS implementations later."""

    name = "console"

    def send(self, notification: Notification) -> None:
        logger.warning("NOTIFICATION [%s] to %s: %s", self.name, notification.recipient, notification.payload)
        notification.status = "delivered"
        notification.sent_at = datetime.now(timezone.utc)


def evaluate_measurement(db: Session, station: Station, measurement: AirMeasurement) -> list[Alert]:
    """Open one alert per active station/metric, or resolve it when the value recovers."""
    created: list[Alert] = []
    for metric, threshold in THRESHOLDS.items():
        value = getattr(measurement, metric)
        active_alerts = list(
            db.scalars(
                select(Alert).where(
                    Alert.station_id == station.id,
                    Alert.metric == metric,
                    Alert.resolved_at.is_(None),
                )
            )
        )
        if value > threshold.value:
            if active_alerts:
                continue
            alert = Alert(
                station_id=station.id,
                measurement_id=measurement.id,
                metric=metric,
                measured_value=value,
                threshold_value=threshold.value,
                severity=severity_for(metric, value),
                message=(
                    f"{station.name}: {threshold.label} = {value:.1f} {threshold.unit}, "
                    f"выше порога {threshold.value:.1f} {threshold.unit}."
                ),
            )
            db.add(alert)
            db.flush()
            notification = Notification(
                alert_id=alert.id,
                channel="console",
                recipient="eco-operator",
                payload={
                    "event": "threshold_exceeded",
                    "station_code": station.code,
                    "station_name": station.name,
                    "metric": metric,
                    "value": value,
                    "threshold": threshold.value,
                    "severity": alert.severity,
                },
            )
            db.add(notification)
            ConsoleNotificationChannel().send(notification)
            created.append(alert)
        else:
            for alert in active_alerts:
                alert.resolved_at = measurement.measured_at
    return created

