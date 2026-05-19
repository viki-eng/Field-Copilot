import axios from 'axios'
import type { Outlet, Rep, Alert, AnalyticsData, ForecastData } from './types'

const http = axios.create({ baseURL: '/api' })

export const fetchOutlets = (type?: string) =>
  http.get<Outlet[]>('/outlets', { params: type ? { type } : {} }).then(r => r.data)

export const fetchReps = () =>
  http.get<Rep[]>('/reps').then(r => r.data)

export const fetchAlerts = () =>
  http.get<Alert[]>('/alerts').then(r => r.data)

export const updateAlertStatus = (id: string, status: string) =>
  http.patch<Alert>(`/alerts/${id}`, { status }).then(r => r.data)

export const fetchAnalytics = () =>
  http.get<AnalyticsData>('/analytics').then(r => r.data)

export const fetchForecast = () =>
  http.get<ForecastData>('/forecast').then(r => r.data)
