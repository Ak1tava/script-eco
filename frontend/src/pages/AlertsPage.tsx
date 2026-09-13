import { useEffect, useState } from 'react'
import { api } from '../api'
import { AlertList } from '../components/AlertList'
import type { Alert } from '../types'

export function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState<number | null>(null)

  const load = async () => {
    try {
      setAlerts(await api.alerts())
      setError(null)
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Не удалось получить предупреждения')
    }
  }
  useEffect(() => { void load() }, [])

  const acknowledge = async (id: number) => {
    setPending(id)
    try {
      const updated = await api.acknowledge(id)
      setAlerts((current) => current.map((alert) => alert.id === id ? updated : alert))
    } finally {
      setPending(null)
    }
  }

  return (
    <section className="alerts-page">
      <p className="eyebrow">Оперативный журнал</p>
      <h1>Предупреждения о превышении</h1>
      <p className="page-lead">Правила срабатывают для каждого нового пакета данных. При первом превышении создаётся предупреждение и записывается уведомление в системный журнал.</p>
      {error && <div className="error-panel">{error}</div>}
      {pending && <div className="toast">Подтверждаем предупреждение…</div>}
      <div className="panel alert-log"><AlertList alerts={alerts} onAcknowledge={(id) => void acknowledge(id)} /></div>
      <aside className="system-note"><b>Как устроено уведомление в MVP</b><span>Событие сохраняется в PostgreSQL и доставляется через console-канал. Для настоящего проекта сюда подключаются Email, Telegram или SMS без изменения логики порогов.</span></aside>
    </section>
  )
}

