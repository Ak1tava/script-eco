export type Measurement = {
  id: number
  station_id: number
  measured_at: string
  pm25: number
  pm10: number
  co: number
  no2: number
  so2: number
  o3: number
  temperature: number
  humidity: number
  aqi: number
  aqi_category: string
  source: string
}

export type Station = {
  id: number
  code: string
  name: string
  district: string
  address: string
  latitude: number
  longitude: number
  is_active: boolean
  is_demo: boolean
  latest_measurement: Measurement | null
  active_alerts_count: number
}

export type StationDetail = Station & { measurements_count: number }

export type Alert = {
  id: number
  station_id: number
  station_name: string | null
  metric: string
  measured_value: number
  threshold_value: number
  severity: 'warning' | 'high' | 'critical'
  message: string
  created_at: string
  acknowledged_at: string | null
  acknowledged_by: string | null
  resolved_at: string | null
}

export type Dashboard = {
  generated_at: string
  stations_total: number
  stations_online: number
  active_alerts: number
  latest_aqi: number | null
  latest_aqi_category: string | null
  stations: Station[]
}

