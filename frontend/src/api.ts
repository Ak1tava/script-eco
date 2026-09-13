import type { Alert, Dashboard, Measurement, StationDetail } from './types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({})) as { detail?: string }
    throw new Error(error.detail || `Ошибка API: ${response.status}`)
  }
  return response.json() as Promise<T>
}

export const api = {
  dashboard: () => request<Dashboard>('/dashboard'),
  station: (id: string) => request<StationDetail>(`/stations/${id}`),
  measurements: (id: string, hours = 24) => request<Measurement[]>(`/stations/${id}/measurements?hours=${hours}`),
  alerts: (activeOnly = true) => request<Alert[]>(`/alerts?active_only=${activeOnly}`),
  acknowledge: (id: number) => request<Alert>(`/alerts/${id}/acknowledge`, {
    method: 'POST',
    body: JSON.stringify({ acknowledged_by: 'dashboard-operator' }),
  }),
}
