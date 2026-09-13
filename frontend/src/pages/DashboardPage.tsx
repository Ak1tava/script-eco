import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { AlertList } from '../components/AlertList'
import { AqiBadge } from '../components/AqiBadge'
import { MetricChart } from '../components/MetricChart'
import { StationMap } from '../components/StationMap'
import type { Alert, Dashboard, Measurement } from '../types'

function LoadingCard() {
  return <div className="loading-card"><span className="spinner" />Получаем тестовые данные…</div>
}

export function DashboardPage() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [history, setHistory] = useState<Measurement[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      try {
        const summary = await api.dashboard()
        const [nextAlerts, nextHistory] = await Promise.all([
          api.alerts(),
          summary.stations[0] ? api.measurements(String(summary.stations[0].id)) : Promise.resolve([]),
        ])
        if (!cancelled) {
          setDashboard(summary)
          setAlerts(nextAlerts)
          setHistory(nextHistory)
          setError(null)
        }
      } catch (loadError) {
        if (!cancelled) setError(loadError instanceof Error ? loadError.message : 'Не удалось подключиться к API')
      }
    }
    void load()
    const refresh = window.setInterval(() => void load(), 30_000)
    return () => { cancelled = true; window.clearInterval(refresh) }
  }, [])

  if (error) return <div className="error-panel"><b>API недоступен.</b><span>{error}</span><code>docker compose up --build</code></div>
  if (!dashboard) return <LoadingCard />

  const selectedStation = dashboard.stations[0]
  return (
    <>
      <section className="hero">
        <div>
          <p className="eyebrow">Караганда · учебный экологический проект</p>
          <h1>Воздух города —<br /><em>в одном окне.</em></h1>
          <p className="hero-copy">Онлайн-панель сети станций. Все показания на этом MVP синтетические и не являются официальными данными о качестве воздуха.</p>
        </div>
        <div className="hero-aqi">
          <span>Индекс по сети сейчас</span>
          <AqiBadge aqi={dashboard.latest_aqi} category={dashboard.latest_aqi_category} />
          <small>Обновлено: {new Intl.DateTimeFormat('ru-RU', { timeStyle: 'short' }).format(new Date(dashboard.generated_at))}</small>
        </div>
      </section>

      <section className="stat-grid" aria-label="Сводные показатели">
        <div className="stat-card"><span className="stat-icon">⌁</span><div><strong>{dashboard.stations_online}/{dashboard.stations_total}</strong><span>станций на связи</span></div></div>
        <div className="stat-card"><span className="stat-icon">◌</span><div><strong>{dashboard.stations_total}</strong><span>точки мониторинга</span></div></div>
        <div className={`stat-card ${dashboard.active_alerts ? 'attention' : ''}`}><span className="stat-icon">!</span><div><strong>{dashboard.active_alerts}</strong><span>активных предупреждений</span></div></div>
      </section>

      <section className="content-grid map-section">
        <div className="panel map-panel">
          <div className="section-heading"><div><p className="eyebrow">Сеть мониторинга</p><h2>Карта станций</h2></div><span className="live-dot">обновляется</span></div>
          <StationMap stations={dashboard.stations} />
        </div>
        <aside className="panel station-panel">
          <div className="section-heading"><div><p className="eyebrow">Последние показания</p><h2>Станции</h2></div></div>
          <div className="station-list">
            {dashboard.stations.map((station) => (
              <Link className="station-item" key={station.id} to={`/stations/${station.id}`}>
                <span className="station-dot" data-tone={station.latest_measurement ? undefined : 'offline'} />
                <span className="station-info"><b>{station.name.replace('Станция ', '')}</b><small>{station.district}</small></span>
                <AqiBadge compact aqi={station.latest_measurement?.aqi ?? null} />
              </Link>
            ))}
          </div>
        </aside>
      </section>

      <section className="content-grid lower-grid">
        <div className="panel chart-panel">
          <div className="section-heading"><div><p className="eyebrow">Динамика</p><h2>{selectedStation?.name || 'История показаний'}</h2></div>{selectedStation && <Link className="text-link" to={`/stations/${selectedStation.id}`}>Подробности →</Link>}</div>
          <MetricChart data={history} />
        </div>
        <aside className="panel alerts-panel">
          <div className="section-heading"><div><p className="eyebrow">Контроль порогов</p><h2>Предупреждения</h2></div><Link className="text-link" to="/alerts">Все →</Link></div>
          <AlertList alerts={alerts.slice(0, 3)} />
        </aside>
      </section>
    </>
  )
}

