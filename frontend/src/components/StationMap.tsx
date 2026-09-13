import { CircleMarker, MapContainer, Popup, TileLayer } from 'react-leaflet'
import { Link } from 'react-router-dom'
import { aqiTone } from './AqiBadge'
import type { Station } from '../types'

const markerColors: Record<string, string> = {
  good: '#2fc78f',
  moderate: '#e7bd35',
  sensitive: '#ed8e37',
  unhealthy: '#e45d4e',
  danger: '#bb3844',
  unknown: '#788884',
}

export function StationMap({ stations }: { stations: Station[] }) {
  return (
    <div className="map-frame" aria-label="Интерактивная карта станций Караганды">
      <MapContainer center={[49.817, 73.096]} zoom={12} scrollWheelZoom className="map">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {stations.map((station) => {
          const latest = station.latest_measurement
          const color = markerColors[aqiTone(latest?.aqi ?? null)]
          return (
            <CircleMarker
              key={station.id}
              center={[station.latitude, station.longitude]}
              radius={latest ? Math.max(10, Math.min(22, latest.aqi / 7)) : 9}
              pathOptions={{ color, fillColor: color, fillOpacity: 0.88, weight: 3 }}
            >
              <Popup>
                <div className="map-popup">
                  <b>{station.name}</b>
                  <span>{station.district}</span>
                  <span>{latest ? `AQI ${latest.aqi} · PM2.5 ${latest.pm25} µg/m³` : 'Ожидание данных'}</span>
                  <Link to={`/stations/${station.id}`}>Открыть станцию →</Link>
                </div>
              </Popup>
            </CircleMarker>
          )
        })}
      </MapContainer>
      <div className="map-legend" aria-label="Легенда AQI">
        <span><i className="legend good" />Хорошее</span>
        <span><i className="legend moderate" />Умеренное</span>
        <span><i className="legend unhealthy" />Высокое</span>
      </div>
    </div>
  )
}

