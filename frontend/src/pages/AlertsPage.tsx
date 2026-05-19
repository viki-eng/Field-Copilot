import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { alerts as initialAlerts } from '../mockData'
import type { Alert } from '../types'
import { Badge } from '../components/Badge'
import { KPICard } from '../components/KPICard'
import { Button } from '../components/Button'
import { Bug, CloudRain, Tag, TrendingUp, AlertCircle, CheckCircle2, ChevronDown, ChevronRight } from 'lucide-react'

const TYPE_ICON_COMPONENT: Record<string, ReactNode> = {
  pest: <Bug size={12} />,
  weather: <CloudRain size={12} />,
  competitor: <Tag size={12} />,
  demand: <TrendingUp size={12} />,
}

interface AlertsPageProps {
  showToast: (msg: string) => void
  onAlertCountChange: (n: number) => void
  viewMode: 'desktop' | 'mobile'
}

export function AlertsPage({ showToast, onAlertCountChange, viewMode }: AlertsPageProps) {
  const [alerts, setAlerts] = useState<Alert[]>(initialAlerts)
  const [dismissing, setDismissing] = useState<Set<string>>(new Set())
  const [showResolved, setShowResolved] = useState(false)

  useEffect(() => {
    onAlertCountChange(initialAlerts.filter(a => a.status === 'active').length)
    const t = setTimeout(() => {
      setAlerts(prev => {
        if (prev.some(a => a.id === 'sim-1')) return prev
        const newAlert: Alert = {
          id: 'sim-1', type: 'pest', severity: 'HIGH', status: 'active',
          title: 'New pest signal — Aphid outbreak risk detected',
          district: 'Ludhiana T002, Punjab', time_ago: 'Just now',
          description: 'AI model detected early aphid activity signals from 6 field reports in last 2 hours. Your wheat growers in T002 are at risk.',
          recommended_action: 'Plan a visit to Jaswant Singh and Gurdev Singh in T002. Recommend Actara 25 WG for aphid management.',
        }
        const updated = [newAlert, ...prev]
        onAlertCountChange(updated.filter(a => a.status === 'active').length)
        showToast('🔔 New alert: Aphid outbreak risk detected')
        return updated
      })
    }, 8000)
    return () => clearTimeout(t)
  }, [])

  const dismiss = (id: string) => {
    setDismissing(prev => new Set(prev).add(id))
    setAlerts(prev => prev.filter(a => a.id !== id))
    onAlertCountChange(alerts.filter(a => a.status === 'active' && a.id !== id).length)
    setDismissing(prev => { const s = new Set(prev); s.delete(id); return s })
  }

  const resolve = (id: string) => {
    setDismissing(prev => new Set(prev).add(id))
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, status: 'resolved' as const } : a))
    onAlertCountChange(alerts.filter(a => a.status === 'active' && a.id !== id).length)
    setDismissing(prev => { const s = new Set(prev); s.delete(id); return s })
    showToast('✓ Alert marked as actioned')
  }

  const active = alerts.filter(a => a.status === 'active')
  const resolved = alerts.filter(a => a.status === 'resolved')

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: 20 }}>
      <div style={{ display: 'grid', gridTemplateColumns: viewMode === 'mobile' ? 'repeat(2, 1fr)' : 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
        <KPICard label="Today's alerts" value={active.length} delta="↑2 since yesterday" deltaType="down" icon={<AlertCircle size={18} style={{ color: '#dc2626' }} />} />
        <KPICard label="Pest risk zones" value={3} delta="Ludhiana T011, T002" icon={<Bug size={18} style={{ color: '#d97706' }} />} />
        <KPICard label="Demand signals" value={2} delta="today" icon={<TrendingUp size={18} style={{ color: '#16a34a' }} />} />
        <KPICard label="Actioned" value={14} delta="this week" deltaType="up" icon={<CheckCircle2 size={18} style={{ color: '#16a34a' }} />} />
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
        {['All', 'Pest', 'Weather', 'Demand', 'Competitor'].map((f, i) => (
          <Button key={f} size="sm" variant={i === 0 ? 'default' : 'outline'}>
            {f}
          </Button>
        ))}
        <select style={{ border: '1px solid var(--border)', borderRadius: 6, padding: '5px 10px', fontSize: 12, marginLeft: 'auto' }}>
          <option>Ludhiana East</option>
          <option>All territories</option>
        </select>
      </div>

      {active.length === 0 && (
        <div style={{ textAlign: 'center', padding: '64px 20px', color: '#6b7280' }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>🌱</div>
          <div style={{ fontWeight: 600, color: '#374151' }}>No active alerts. Territory looking healthy 🌱</div>
        </div>
      )}

      {active.map(a => (
        <div key={a.id} style={{
          background: 'white', border: '1px solid var(--border)', borderRadius: 8,
          padding: 20, marginBottom: 12,
          opacity: dismissing.has(a.id) ? 0.5 : 1,
          transition: 'opacity 0.3s',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Badge level={a.severity} />
              <span style={{ fontSize: 11, background: '#f3f4f6', padding: '2px 8px', borderRadius: 9999, display: 'flex', alignItems: 'center', gap: 4 }}>
                {TYPE_ICON_COMPONENT[a.type]} {a.type.toUpperCase()}
              </span>
            </div>
            <span style={{ fontSize: 11, color: '#6b7280' }}>{a.time_ago}</span>
          </div>
          <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>{a.title}</div>
          <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 8 }}>{a.district}</div>
          <div style={{ fontSize: 13, color: '#374151', marginBottom: 10 }}>{a.description}</div>
          <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 6, padding: 10 }}>
            <div style={{ fontWeight: 600, color: '#166534', marginBottom: 4, fontSize: 12 }}>RECOMMENDED ACTION:</div>
            <div style={{ fontSize: 13, color: '#15803d' }}>{a.recommended_action}</div>
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 14, flexWrap: 'wrap' }}>
            <Button variant="default" onClick={() => { showToast('✓ Visit planned'); dismiss(a.id) }}>
              Plan visit
            </Button>
            <Button variant="outline" onClick={() => dismiss(a.id)}>
              Dismiss
            </Button>
            <Button variant="outline" style={{ color: '#16a34a', borderColor: '#16a34a' }} onClick={() => resolve(a.id)}>
              Mark resolved ✓
            </Button>
          </div>
        </div>
      ))}

      {resolved.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowResolved(!showResolved)}
            style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#6b7280' }}
          >
            {showResolved ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            <span>Actioned ({resolved.length})</span>
          </Button>
          {showResolved && resolved.map(a => (
            <div key={a.id} style={{ background: 'white', border: '1px dashed var(--border)', borderRadius: 8, padding: 14, marginTop: 8, opacity: 0.65 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 500 }}>{a.title}</span>
                <span style={{ fontSize: 11, background: '#dcfce7', color: '#16a34a', padding: '2px 8px', borderRadius: 4 }}>Actioned</span>
              </div>
              <div style={{ fontSize: 12, color: '#6b7280' }}>{a.district}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
