from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MeasurementIn(BaseModel):
    """The stable sensor payload contract used by both devices and the simulator."""

    station_code: str = Field(min_length=3, max_length=32)
    measured_at: datetime
    pm25: float = Field(ge=0, le=2_000, description="PM2.5, µg/m³")
    pm10: float = Field(ge=0, le=2_000, description="PM10, µg/m³")
    co: float = Field(ge=0, le=200, description="CO, mg/m³")
    no2: float = Field(ge=0, le=2_000, description="NO₂, µg/m³")
    so2: float = Field(ge=0, le=2_000, description="SO₂, µg/m³")
    o3: float = Field(ge=0, le=2_000, description="O₃, µg/m³")
    temperature: float = Field(ge=-60, le=70, description="°C")
    humidity: float = Field(ge=0, le=100, description="%")
    source: str = Field(default="simulator", max_length=32)


class MeasurementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    station_id: int
    measured_at: datetime
    pm25: float
    pm10: float
    co: float
    no2: float
    so2: float
    o3: float
    temperature: float
    humidity: float
    aqi: int
    aqi_category: str
    source: str


class LatestMeasurementOut(MeasurementOut):
    pass


class StationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    district: str
    address: str
    latitude: float
    longitude: float
    is_active: bool
    is_demo: bool
    latest_measurement: LatestMeasurementOut | None = None
    active_alerts_count: int = 0


class StationDetailOut(StationOut):
    measurements_count: int


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    station_id: int
    metric: str
    measured_value: float
    threshold_value: float
    severity: str
    message: str
    created_at: datetime
    acknowledged_at: datetime | None
    acknowledged_by: str | None
    resolved_at: datetime | None
    station_name: str | None = None


class AcknowledgeAlertIn(BaseModel):
    acknowledged_by: str = Field(default="operator", min_length=2, max_length=120)


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alert_id: int
    channel: str
    recipient: str
    status: str
    payload: dict
    sent_at: datetime | None
    created_at: datetime


class DashboardOut(BaseModel):
    generated_at: datetime
    stations_total: int
    stations_online: int
    active_alerts: int
    latest_aqi: int | None
    latest_aqi_category: str | None
    stations: list[StationOut]


class IngestResult(BaseModel):
    measurement: MeasurementOut
    created_alert_ids: list[int]

