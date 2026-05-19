export interface Outlet {
  id: string
  name: string
  type: 'retailer' | 'farmer'
  lat: number
  lng: number
  priority_score: number
  priority_level: 'HIGH' | 'MEDIUM' | 'LOW'
  last_visit_days_ago: number
  last_order_value: number
  inventory_pct: number
  crop_stage: string | null
  pest_risk: 'HIGH' | 'MEDIUM' | 'LOW'
  ai_recommendation: string
  talking_points: string[]
}

export interface Rep {
  id: string
  name: string
  initials: string
  territory: string
  status: 'active' | 'idle' | 'offline'
  current_location: string
  visits_today: number
  visits_target: number
  conversion_rate: number
  mtd_revenue: number
  ai_adoption: number
  trend: 'up' | 'down' | 'neutral'
}

export interface Alert {
  id: string
  type: 'pest' | 'weather' | 'competitor' | 'demand'
  severity: 'HIGH' | 'MEDIUM' | 'LOW'
  status: 'active' | 'resolved' | 'dismissed'
  title: string
  district: string
  time_ago: string
  description: string
  recommended_action: string
}

export interface AnalyticsData {
  kpis: {
    total_visits: number
    total_visits_delta: number
    conversion_rate: number
    conversion_rate_delta: number
    avg_order_value: number
    avg_order_value_delta: number
    ai_adoption: number
    ai_adoption_delta: number
  }
  weekly_visits: { day: string; visits: number; conversion: number }[]
  product_revenue: { product: string; revenue: number }[]
  rep_performance: {
    name: string; territory: string; visits: number
    conversion_rate: number; revenue: number; ai_adoption: number; trend: string
  }[]
}

export interface ForecastData {
  chart_data: { date: string; predicted: number; baseline: number; low: number; high: number }[]
  district_breakdown: {
    district: string; stock: number; demand: number; gap: number; urgency: string
  }[]
}
