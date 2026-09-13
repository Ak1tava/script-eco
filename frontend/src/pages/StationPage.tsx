import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import { AlertList } from '../components/AlertList'
import { AqiBadge } from '../components/AqiBadge'
import { MetricChart, type ChartMetric } from '../components/MetricChart'
import type { Alert, Measurement, StationDetail } from '../types'

const pollutantLabels: Array<{ key: keyof Measurement; label: string; unit: string; limit?: number }> = [
  { key: 'pm25', label: 'PM2.5', unit: 'µg/m³', limit: 55 },
  { key: 'pm10', label: 'PM10', unit: 'µg/m³', limit: 150 },
  { key: 'no2', label: 'NO₂', unit: 'µg/m³', limit: 200 },
  { key: 'so2', label: 'SO₂', unit: 'µg/m³', limit: 350 },
  { key: 'o3', label: 'O₃', unit: 'µg/m³', limit: 180 },
  { key: 'co', label: 'CO', unit: 'mg/m³', limit: 10 },
]

export function StationPage() {
  const { id = '' } = useParams()
  const [station, setStation] = useState<StationDetail | null>(null)
  const [measurements, setMeasurements] = useState<Measurement[]>([])
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [hours, setHours] = useState(24)
  const [metric, setMetric] = useState<ChartMetric>('pm25')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      try {
        const [nextStation, nextMeasurements, nextAlerts] = await Promise.all([
          api.station(id), api.measurements(id, hours), api.alerts(),
        ])
        if (!cancelled) {
          setStation(nextStation)
          setMeasurements(nextMeasurements)
          setAlerts(nextAlerts.filter((alert) => alert.station_id === nextStation.id))
          setError(null)
        }
      } catch (loadError) {
        if (!cancelled) setError(loadError instanceof Error ? loadError.message : 'Станция недоступна')
      }
    }
    void load()
    return () => { cancelled = true }
  }, [id, hours])

  const last = station?.latest_measurement
  const chartMetrics = useMemo(() => [metric, metric === 'pm25' ? 'pm10' : 'pm25'] as ChartMetric[], [metric])

  if (error) return <div className="error-panel"><b>Не удалось открыть станцию.</b><span>{error}</span><Link to="/">Вернуться на карту</Link></div>
  if (!station || !last) return <div className="loading-card"><span className="spinner" />Загружаем станцию…</div>

  return (
    <>
      <Link className="back-link" to="/">← Все станции</Link>
      <section className="station-hero">
        <div>
          <p className="eyebrow">{station.code} · {station.district}</p>
          <h1>{station.name}</h1>
          <p>{station.address} · <span className="demo-pill">ТЕСТОВЫЕ ДАННЫЕ</span></p>
        </div>
        <AqiBadge aqi={last.aqi} category={last.aqi_category} />
      </section>

      <section className="metric-grid" aria-label="Последние показатели станции">
        {pollutantLabels.map((pollutant) => {
          const value = last[pollutant.key] as number
          const ratio = pollutant.limit ? value / pollutant.limit : 0
          return (
            <article className={`metric-card ${ratio > 1 ? 'over-limit' : ''}`} key={pollutant.key}>
              <span>{pollutant.label}</span>
              <strong>{value.toFixed(pollutant.key === 'co' ? 2 : 1)}</strong>
              <small>{pollutant.unit}{pollutant.limit ? ` · порог ${pollutant.limit}` : ''}</small>
              {pollutant.limit && <i className="meter"><i style={{ width: `${Math.min(ratio * 100, 100)}%` }} /></i>}
            </article>
          )
        })}
        <article className="metric-card weather"><span>Условия</span><strong>{last.temperature.toFixed(1)}°</strong><small>влажность {last.humidity.toFixed(0)}%</small></article>
      </section>

      <section className="panel detail-chart">
        <div className="section-heading wrap-mobile"><div><p className="eyebrow">Исторические значения</p><h2>Динамика загрязнения</h2></div><div className="chart-controls"><select value={hours} onChange={(event) => setHours(Number(event.target.value))}><option value={6}>6 часов</option><option value={24}>24 часа</option><option value={72}>3 дня</option><option value={168}>7 дней</option></select><select value={metric} onChange={(event) => setMetric(event.target.value as ChartMetric)}><option value="pm25">PM2.5</option><option value="pm10">PM10</option><option value="no2">NO₂</option><option value="aqi">AQI</option></select></div></div>
        <MetricChart data={measurements} metrics={chartMetrics} />
      </section>

      <section className="content-grid station-bottom">
        <article className="panel station-facts"><p className="eyebrow">Статус оборудования</p><h2>Станция на связи</h2><dl><div><dt>Последний пакет</dt><dd>{new Intl.DateTimeFormat('ru-RU', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(last.measured_at))}</dd></div><div><dt>Источник</dt><dd>Программный симулятор</dd></div><div><dt>Точек в истории</dt><dd>{station.measurements_count}</dd></div></dl></article>
        <article className="panel"><div className="section-heading"><div><p className="eyebrow">Контроль станции</p><h2>Активные предупреждения</h2></div></div><AlertList alerts={alerts} /></article>
      </section>
    </>
  )
}

