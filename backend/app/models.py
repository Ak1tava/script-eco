from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Station(Base):
    __tablename__ = "stations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    district: Mapped[str] = mapped_column(String(120))
    address: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    ingest_token: Mapped[str] = mapped_column(String(128), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    measurements: Mapped[list[AirMeasurement]] = relationship(back_populates="station", cascade="all, delete-orphan")
    alerts: Mapped[list[Alert]] = relationship(back_populates="station", cascade="all, delete-orphan")


class AirMeasurement(Base):
    __tablename__ = "air_measurements"
    __table_args__ = (
        UniqueConstraint("station_id", "measured_at", name="uq_measurement_station_time"),
        Index("ix_measurement_station_time", "station_id", "measured_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), index=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    pm25: Mapped[float] = mapped_column(Float)
    pm10: Mapped[float] = mapped_column(Float)
    co: Mapped[float] = mapped_column(Float)
    no2: Mapped[float] = mapped_column(Float)
    so2: Mapped[float] = mapped_column(Float)
    o3: Mapped[float] = mapped_column(Float)
    temperature: Mapped[float] = mapped_column(Float)
    humidity: Mapped[float] = mapped_column(Float)
    aqi: Mapped[int] = mapped_column(Integer, index=True)
    aqi_category: Mapped[str] = mapped_column(String(32))
    source: Mapped[str] = mapped_column(String(32), default="simulator")
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    station: Mapped[Station] = relationship(back_populates="measurements")
    alerts: Mapped[list[Alert]] = relationship(back_populates="measurement")


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (Index("ix_alert_active_station_metric", "station_id", "metric", "resolved_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), index=True)
    measurement_id: Mapped[int] = mapped_column(ForeignKey("air_measurements.id"))
    metric: Mapped[str] = mapped_column(String(32))
    measured_value: Mapped[float] = mapped_column(Float)
    threshold_value: Mapped[float] = mapped_column(Float)
    severity: Mapped[str] = mapped_column(String(16))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    station: Mapped[Station] = relationship(back_populates="alerts")
    measurement: Mapped[AirMeasurement] = relationship(back_populates="alerts")
    notifications: Mapped[list[Notification]] = relationship(back_populates="alert", cascade="all, delete-orphan")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), index=True)
    channel: Mapped[str] = mapped_column(String(32), default="console")
    recipient: Mapped[str] = mapped_column(String(120), default="eco-operator")
    status: Mapped[str] = mapped_column(String(32), default="queued")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    alert: Mapped[Alert] = relationship(back_populates="notifications")
