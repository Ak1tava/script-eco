import { Link } from 'react-router-dom'
import type { Alert } from '../types'

const severityLabel = { warning: 'Внимание', high: 'Высокий', critical: 'Критический' }

export function AlertList({ alerts, onAcknowledge }: { alerts: Alert[]; onAcknowledge?: (id: number) => void }) {
  if (alerts.length === 0) {
    return <div className="empty-state"><span>✓</span> Активных превышений сейчас нет.</div>
  }
  return (
    <div className="alert-list">
      {alerts.map((alert) => (
        <article className={`alert-row ${alert.severity}`} key={alert.id}>
          <div className="alert-signal" />
          <div className="alert-copy">
            <div className="alert-title">
              <span className={`severity ${alert.severity}`}>{severityLabel[alert.severity]}</span>
              <Link to={`/stations/${alert.station_id}`}>{alert.station_name || `Станция #${alert.station_id}`}</Link>
            </div>
            <p>{alert.message}</p>
            <small>{new Intl.DateTimeFormat('ru-RU', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(alert.created_at))}</small>
          </div>
          {onAcknowledge && (
            <button className="text-button" onClick={() => onAcknowledge(alert.id)} disabled={Boolean(alert.acknowledged_at)}>
              {alert.acknowledged_at ? 'Принято' : 'Подтвердить'}
            </button>
          )}
        </article>
      ))}
    </div>
  )
}

