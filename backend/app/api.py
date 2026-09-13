from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AirMeasurement, Alert, Notification, Station
from app.schemas import (
    AcknowledgeAlertIn,
    AlertOut,
    DashboardOut,
    IngestResult,
    MeasurementIn,
    MeasurementOut,
    NotificationOut,
    StationDetailOut,
    StationOut,
)
from app.services.air_quality import calculate_aqi
from app.services.alerts import evaluate_measurement

router = APIRouter(prefix="/api/v1", tags=["monitoring"])


def _latest_rows(db: Session) -> list[tuple[Station, AirMeasurement | None]]:
    latest_times = (
        select(AirMeasurement.station_id, func.max(AirMeasurement.measured_at).label("latest_at"))
        .group_by(AirMeasurement.station_id)
        .subquery()
    )
    return list(
        db.execute(
            select(Station, AirMeasurement)
            .outerjoin(latest_times, Station.id == latest_times.c.station_id)
            .outerjoin(
                AirMeasurement,
                and_(
                    AirMeasurement.station_id == latest_times.c.station_id,
                    AirMeasurement.measured_at == latest_times.c.latest_at,
                ),
            )
            .order_by(Station.code)
        ).all()
    )


def _active_alert_counts(db: Session) -> dict[int, int]:
    return dict(
        db.execute(
            select(Alert.station_id, func.count(Alert.id))
            .where(Alert.resolved_at.is_(None))
            .group_by(Alert.station_id)
        ).all()
    )


def _station_out(station: Station, latest: AirMeasurement | None, active_count: int) -> StationOut:
    data = StationOut.model_validate(station).model_dump()
    data["latest_measurement"] = latest
    data["active_alerts_count"] = active_count
    return StationOut(**data)


@router.get("/dashboard", response_model=DashboardOut)
def get_dashboard(db: Session = Depends(get_db)) -> DashboardOut:
    rows = _latest_rows(db)
    alert_counts = _active_alert_counts(db)
    stations = [_station_out(station, latest, alert_counts.get(station.id, 0)) for station, latest in rows]
    aqis = [station.latest_measurement.aqi for station in stations if station.latest_measurement]
    latest_aqi = max(aqis) if aqis else None
    latest_category = next(
        (station.latest_measurement.aqi_category for station in stations if station.latest_measurement and station.latest_measurement.aqi == latest_aqi),
        None,
    )
    return DashboardOut(
        generated_at=datetime.now(timezone.utc),
        stations_total=len(stations),
        stations_online=sum(1 for station in stations if station.is_active and station.latest_measurement),
        active_alerts=sum(alert_counts.values()),
        latest_aqi=latest_aqi,
        latest_aqi_category=latest_category,
        stations=stations,
    )


@router.get("/stations", response_model=list[StationOut])
def list_stations(db: Session = Depends(get_db)) -> list[StationOut]:
    counts = _active_alert_counts(db)
    return [_station_out(station, latest, counts.get(station.id, 0)) for station, latest in _latest_rows(db)]


@router.get("/stations/{station_id}", response_model=StationDetailOut)
def get_station(station_id: int, db: Session = Depends(get_db)) -> StationDetailOut:
    station = db.get(Station, station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Станция не найдена")
    latest = db.scalar(
        select(AirMeasurement).where(AirMeasurement.station_id == station_id).order_by(AirMeasurement.measured_at.desc()).limit(1)
    )
    count = db.scalar(select(func.count(AirMeasurement.id)).where(AirMeasurement.station_id == station_id)) or 0
    data = _station_out(station, latest, _active_alert_counts(db).get(station.id, 0)).model_dump()
    data["measurements_count"] = count
    return StationDetailOut(**data)


@router.get("/stations/{station_id}/measurements", response_model=list[MeasurementOut])
def get_measurements(
    station_id: int,
    hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(get_db),
) -> list[AirMeasurement]:
    if not db.get(Station, station_id):
        raise HTTPException(status_code=404, detail="Станция не найдена")
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    return list(
        db.scalars(
            select(AirMeasurement)
            .where(AirMeasurement.station_id == station_id, AirMeasurement.measured_at >= since)
            .order_by(AirMeasurement.measured_at.asc())
            .limit(2_100)
        )
    )


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(
    active_only: bool = True,
    station_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[AlertOut]:
    query = select(Alert, Station.name).join(Station, Alert.station_id == Station.id)
    if active_only:
        query = query.where(Alert.resolved_at.is_(None))
    if station_id:
        query = query.where(Alert.station_id == station_id)
    rows = db.execute(query.order_by(Alert.created_at.desc()).limit(200)).all()
    return [AlertOut(**AlertOut.model_validate(alert).model_dump(), station_name=station_name) for alert, station_name in rows]


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge_alert(
    alert_id: int,
    body: AcknowledgeAlertIn,
    db: Session = Depends(get_db),
) -> AlertOut:
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Предупреждение не найдено")
    if alert.acknowledged_at is None:
        alert.acknowledged_at = datetime.now(timezone.utc)
        alert.acknowledged_by = body.acknowledged_by
        db.commit()
        db.refresh(alert)
    return AlertOut(**AlertOut.model_validate(alert).model_dump(), station_name=alert.station.name)


@router.get("/notifications", response_model=list[NotificationOut])
def list_notifications(db: Session = Depends(get_db)) -> list[Notification]:
    return list(db.scalars(select(Notification).order_by(Notification.created_at.desc()).limit(100)))


@router.post("/ingest/measurements", response_model=IngestResult, status_code=status.HTTP_201_CREATED)
def ingest_measurement(
    payload: MeasurementIn,
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> IngestResult:
    """Endpoint physical devices will use. Retries are safe by station+timestamp."""
    station = db.scalar(select(Station).where(Station.code == payload.station_code))
    if not station or not station.is_active:
        raise HTTPException(status_code=404, detail="Активная станция не найдена")
    if not x_api_key or x_api_key != station.ingest_token:
        raise HTTPException(status_code=401, detail="Неверный ключ станции")
    existing = db.scalar(
        select(AirMeasurement).where(
            AirMeasurement.station_id == station.id,
            AirMeasurement.measured_at == payload.measured_at,
        )
    )
    if existing:
        return IngestResult(measurement=existing, created_alert_ids=[])

    aqi = calculate_aqi(payload.pm25, payload.pm10)
    data = payload.model_dump(exclude={"station_code"})
    measurement = AirMeasurement(
        station_id=station.id,
        aqi=aqi.value,
        aqi_category=aqi.category,
        **data,
    )
    db.add(measurement)
    db.flush()
    alerts = evaluate_measurement(db, station, measurement)
    db.commit()
    db.refresh(measurement)
    return IngestResult(measurement=measurement, created_alert_ids=[alert.id for alert in alerts])

