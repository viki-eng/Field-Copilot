import { useState } from 'react'
import { forecastData, districtForecast, campaignStats } from '../mockData'
import { Badge } from '../components/Badge'
import { Button } from '../components/Button'
import { Card, CardHeader, CardTitle, CardContent } from '../components/Card'
import { CloudRain, Bug } from 'lucide-react'
import {
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ComposedChart, Line, Area,
} from 'recharts'

interface ForecastPageProps { viewMode: 'desktop' | 'mobile' }

export function ForecastPage({ viewMode }: ForecastPageProps) {
  const [horizon, setHorizon] = useState(0)

  const urgencyLevel = (u: string) => u === 'HIGH' ? 'HIGH' : u === 'MEDIUM' ? 'MEDIUM' : 'OK'

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: 20 }}>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 20, flexWrap: 'wrap' }}>
        <label style={{ fontSize: 13, color: '#6b7280' }}>Product:</label>
        <select style={{ border: '1px solid var(--border)', borderRadius: 6, padding: '6px 10px' }}>
          {['Tilt 250 EC', 'Amistar 250 SC', 'Axial 50 EC', 'Vertimec 1.8 EC'].map(p => <option key={p}>{p}</option>)}
        </select>
        <label style={{ fontSize: 13, color: '#6b7280' }}>Tehsil:</label>
        <select style={{ border: '1px solid var(--border)', borderRadius: 6, padding: '6px 10px' }}>
          {['All Ludhiana East', 'T001', 'T002', 'T006', 'T009', 'T011'].map(d => <option key={d}>{d}</option>)}
        </select>
        <label style={{ fontSize: 13, color: '#6b7280' }}>Horizon:</label>
        {['7 days', '30 days'].map((h, i) => (
          <Button
            key={h}
            size="sm"
            variant={horizon === i ? 'default' : 'outline'}
            onClick={() => setHorizon(i)}
          >
            {h}
          </Button>
        ))}
      </div>

      <Card style={{ marginBottom: 20 }}>
        <CardHeader>
          <CardTitle style={{ fontSize: 13 }}>
            Predicted demand — Tilt 250 EC · Ludhiana East · Next {horizon === 0 ? '7' : '30'} days
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={220}>
            <ComposedChart data={forecastData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Area type="monotone" dataKey="high" fill="#dcfce7" stroke="transparent" name="Confidence high" />
              <Area type="monotone" dataKey="low" fill="white" stroke="transparent" name="Confidence low" />
              <Line type="monotone" dataKey="baseline" stroke="#9ca3af" strokeDasharray="5 5" strokeWidth={2} dot={false} name="Historical baseline" />
              <Line type="monotone" dataKey="predicted" stroke="#16a34a" strokeWidth={2} dot={{ r: 4 }} name="Predicted demand" />
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div style={{ display: 'grid', gridTemplateColumns: viewMode === 'mobile' ? '1fr' : '1fr 300px', gap: 16 }}>
        <Card style={{ overflow: 'hidden' }}>
          <CardHeader>
            <CardTitle style={{ fontSize: 13 }}>Tehsil breakdown</CardTitle>
          </CardHeader>
          <CardContent style={{ padding: 0 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr>
                  {['Tehsil', 'Current stock', 'Predicted demand (7d)', 'Gap', 'Urgency'].map(h => (
                    <th key={h} style={{ textAlign: 'left', padding: '10px 14px', fontSize: 11, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', borderBottom: '1px solid var(--border)' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {districtForecast.map((d, i) => (
                  <tr key={d.tehsil} style={{ background: i % 2 === 1 ? '#f9fafb' : 'white' }}>
                    <td style={{ padding: '10px 14px', fontWeight: 500 }}>{d.tehsil}</td>
                    <td style={{ padding: '10px 14px' }}>{d.stock} units</td>
                    <td style={{ padding: '10px 14px' }}>{d.demand} units</td>
                    <td style={{ padding: '10px 14px', color: d.gap < 0 ? '#dc2626' : '#16a34a', fontWeight: 600 }}>
                      {d.gap > 0 ? '+' : ''}{d.gap}
                    </td>
                    <td style={{ padding: '10px 14px' }}><Badge level={urgencyLevel(d.urgency)} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <CardHeader>
              <CardTitle>What-if scenarios</CardTitle>
            </CardHeader>
            <CardContent>
              {[
                { title: 'If rainfall increases 20%:', icon: <CloudRain size={14} style={{ display: 'inline', marginRight: 4 }} />, effects: ['Fungicide demand +35%', 'Seed treatment demand -8%'] },
                { title: 'If pest alert escalates:', icon: <Bug size={14} style={{ display: 'inline', marginRight: 4 }} />, effects: ['Insecticide demand +60%', 'Need 6 additional visits in T011'] },
              ].map(s => (
                <div key={s.title} style={{ marginBottom: 16 }}>
                  <div style={{ fontWeight: 600, marginBottom: 6, fontSize: 13, display: 'flex', alignItems: 'center' }}>
                    {s.icon}{s.title}
                  </div>
                  {s.effects.map(e => (
                    <div key={e} style={{ fontSize: 12, color: '#16a34a', marginBottom: 2 }}>→ {e}</div>
                  ))}
                </div>
              ))}
            </CardContent>
          </Card>

          <Card style={{ marginTop: 0 }}>
            <CardHeader><CardTitle style={{ fontSize: 13 }}>📱 WhatsApp Campaign — Tilt 250 EC</CardTitle></CardHeader>
            <CardContent>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                {[
                  ['Sent', campaignStats.sent],
                  ['Delivered', campaignStats.delivered],
                  ['Opened', campaignStats.opened],
                  ['Clicked', campaignStats.clicked],
                ].map(([label, val]) => (
                  <div key={String(label)}>
                    <div style={{ fontSize: 11, color: '#6b7280' }}>{label}</div>
                    <div style={{ fontSize: 20, fontWeight: 700, color: '#0f172a' }}>{val}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
