import { useEffect, useState } from 'react'
import { fetchReps } from '../api'
import type { Rep } from '../types'
import { ProgressBar } from '../components/ProgressBar'
import { Button } from '../components/Button'
import { Card, CardContent } from '../components/Card'
import { MapPin, Send, Wifi, WifiOff, Coffee } from 'lucide-react'

const STATUS_COLOR = { active: '#16a34a', idle: '#d97706', offline: '#9ca3af' }
const STATUS_LABEL = { active: 'Active', idle: 'Idle', offline: 'Offline' }
const TREND_COLOR = { up: '#16a34a', down: '#dc2626', neutral: '#6b7280' }
const TREND_ICON = { up: '↑', down: '↓', neutral: '→' }

const STATUS_WIFI_ICON = {
  active: <Wifi size={12} style={{ color: '#16a34a' }} />,
  idle: <Coffee size={12} style={{ color: '#d97706' }} />,
  offline: <WifiOff size={12} style={{ color: '#9ca3af' }} />,
}

interface RepsPageProps { showToast: (msg: string) => void; viewMode: 'desktop' | 'mobile' }

export function RepsPage({ showToast, viewMode }: RepsPageProps) {
  const [reps, setReps] = useState<Rep[]>([])

  useEffect(() => { fetchReps().then(setReps) }, [])

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: 20 }}>
      <div style={{ display: 'grid', gridTemplateColumns: viewMode === 'mobile' ? '1fr' : 'repeat(3, 1fr)', gap: 16 }}>
        {reps.map(r => (
          <Card key={r.id}>
            <CardContent style={{ padding: 20 }}>
              <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start', marginBottom: 16 }}>
                <div style={{
                  width: 40, height: 40, background: '#16a34a', borderRadius: '50%',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: 'white', fontSize: 13, fontWeight: 600, flexShrink: 0,
                }}>{r.initials}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{r.name}</div>
                  <div style={{ fontSize: 12, color: '#6b7280' }}>{r.territory}</div>
                  <div style={{ fontSize: 12, marginTop: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: STATUS_COLOR[r.status], display: 'inline-block' }} />
                    {STATUS_WIFI_ICON[r.status]}
                    <span style={{ color: STATUS_COLOR[r.status] }}>{STATUS_LABEL[r.status]}</span>
                    {r.status === 'active' && r.current_location && (
                      <span style={{ color: '#6b7280' }}> — at {r.current_location}</span>
                    )}
                  </div>
                </div>
              </div>

              <div style={{ marginBottom: 14 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                  <span style={{ color: '#6b7280' }}>Visits today</span>
                  <span style={{ fontWeight: 500 }}>{r.visits_today}/{r.visits_target}</span>
                </div>
                <ProgressBar pct={(r.visits_today / r.visits_target) * 100} />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12, fontSize: 12 }}>
                <div>
                  <div style={{ color: '#6b7280' }}>Conv. rate</div>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{r.conversion_rate}%</div>
                </div>
                <div>
                  <div style={{ color: '#6b7280' }}>MTD revenue</div>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>₹{(r.mtd_revenue / 100000).toFixed(1)}L</div>
                </div>
              </div>

              <div style={{ fontSize: 12, marginBottom: 14 }}>
                <span style={{ color: '#6b7280' }}>AI adoption: </span>
                <span style={{ fontWeight: 600, color: TREND_COLOR[r.trend] }}>
                  {r.ai_adoption}% {TREND_ICON[r.trend]}
                </span>
              </div>

              <div style={{ display: 'flex', gap: 8 }}>
                <Button variant="outline" size="sm" style={{ flex: 1 }} onClick={() => showToast(`Opening route for ${r.name}...`)}>
                  <MapPin size={13} style={{ marginRight: 4 }} /> View route
                </Button>
                <Button variant="outline" size="sm" style={{ flex: 1 }} onClick={() => showToast(`✓ Alert sent to ${r.name}`)}>
                  <Send size={13} style={{ marginRight: 4 }} /> Send alert
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
