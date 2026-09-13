type Props = { aqi: number | null; category?: string | null; compact?: boolean }

function tone(aqi: number | null): string {
  if (aqi === null) return 'unknown'
  if (aqi <= 50) return 'good'
  if (aqi <= 100) return 'moderate'
  if (aqi <= 150) return 'sensitive'
  if (aqi <= 200) return 'unhealthy'
  return 'danger'
}

export function AqiBadge({ aqi, category, compact = false }: Props) {
  if (aqi === null) return <span className="aqi-badge unknown">Нет данных</span>
  return (
    <span className={`aqi-badge ${tone(aqi)} ${compact ? 'compact' : ''}`} title={category || undefined}>
      <strong>AQI {aqi}</strong>
      {!compact && <small>{category}</small>}
    </span>
  )
}

export function aqiTone(aqi: number | null): string {
  return tone(aqi)
}

