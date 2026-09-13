import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { Measurement } from '../types'

const fields = {
  pm25: { label: 'PM2.5', color: '#54d6b4', unit: 'µg/m³' },
  pm10: { label: 'PM10', color: '#e8b341', unit: 'µg/m³' },
  no2: { label: 'NO₂', color: '#d87563', unit: 'µg/m³' },
  aqi: { label: 'AQI', color: '#a99aef', unit: '' },
} as const

export type ChartMetric = keyof typeof fields

function timeLabel(value: string): string {
  return new Intl.DateTimeFormat('ru-RU', { hour: '2-digit', minute: '2-digit' }).format(new Date(value))
}

export function MetricChart({ data, metrics = ['pm25', 'pm10'] }: { data: Measurement[]; metrics?: ChartMetric[] }) {
  const visible = metrics.map((metric) => fields[metric])
  return (
    <div className="chart-wrap">
      <ResponsiveContainer width="100%" height={285}>
        <LineChart data={data} margin={{ top: 8, right: 12, left: -14, bottom: 0 }}>
          <CartesianGrid stroke="#dce8e2" strokeDasharray="3 5" vertical={false} />
          <XAxis dataKey="measured_at" tickFormatter={timeLabel} minTickGap={30} tick={{ fill: '#687a73', fontSize: 12 }} />
          <YAxis tick={{ fill: '#687a73', fontSize: 12 }} />
          <Tooltip
            labelFormatter={timeLabel}
            formatter={(value: number, name: string) => [`${value} ${fields[name as ChartMetric]?.unit || ''}`, fields[name as ChartMetric]?.label || name]}
            contentStyle={{ borderRadius: 12, border: '1px solid #dce8e2', boxShadow: '0 10px 28px #11352a19' }}
          />
          <Legend formatter={(value) => fields[value as ChartMetric]?.label || value} />
          {metrics.map((metric) => <Line key={metric} type="monotone" dataKey={metric} stroke={fields[metric].color} strokeWidth={2.6} dot={false} activeDot={{ r: 4 }} />)}
        </LineChart>
      </ResponsiveContainer>
      <p className="chart-caption">{visible.map((item) => item.label).join(' · ')} · последние 24 часа</p>
    </div>
  )
}

