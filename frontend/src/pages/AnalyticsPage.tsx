import { myPerformance, weeklyVisits, productRevenue, visitLog } from '../mockData'
import { KPICard } from '../components/KPICard'
import { Button } from '../components/Button'
import { Card, CardHeader, CardTitle, CardContent } from '../components/Card'
import { Download, Activity, BarChart2, Target, Bot } from 'lucide-react'
import {
  Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ComposedChart, Line, BarChart,
} from 'recharts'

interface AnalyticsPageProps { viewMode: 'desktop' | 'mobile' }

export function AnalyticsPage({ viewMode }: AnalyticsPageProps) {
  const trendArrow = (v: number) => v > 0 ? '↑' : '↓'
  const trendType = (v: number): 'up' | 'down' => v > 0 ? 'up' : 'down'

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: 20 }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        {['Last 7 days', 'Ludhiana East'].map(o => (
          <select key={o} style={{ border: '1px solid var(--border)', borderRadius: 6, padding: '6px 10px' }}>
            <option>{o}</option>
          </select>
        ))}
        <Button variant="outline" size="sm" style={{ marginLeft: 'auto' }}>
          <Download size={14} style={{ marginRight: 4 }} /> Export CSV
        </Button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: viewMode === 'mobile' ? 'repeat(2, 1fr)' : 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
        <KPICard label="My visits this week" value={myPerformance.visits_this_week} delta={`${trendArrow(5)}5% vs last week`} deltaType={trendType(5)} icon={<Activity size={18} />} />
        <KPICard label="My conversion rate" value={`${myPerformance.conversion_rate}%`} delta={`${trendArrow(myPerformance.conversion_rate_delta)}${Math.abs(myPerformance.conversion_rate_delta)}% vs avg`} deltaType={trendType(myPerformance.conversion_rate_delta)} icon={<Target size={18} />} />
        <KPICard label="Avg order value" value={`₹${myPerformance.avg_order_value.toLocaleString('en-IN')}`} delta={`${trendArrow(myPerformance.avg_order_delta)}${Math.abs(myPerformance.avg_order_delta)}% vs avg`} deltaType={trendType(myPerformance.avg_order_delta)} icon={<BarChart2 size={18} />} />
        <KPICard label="AI tool usage" value={`${myPerformance.ai_adoption}%`} delta={`${trendArrow(myPerformance.ai_adoption_delta)}${Math.abs(myPerformance.ai_adoption_delta)}% vs last week`} deltaType={trendType(myPerformance.ai_adoption_delta)} icon={<Bot size={18} />} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: viewMode === 'mobile' ? '1fr' : '1fr 1fr', gap: 16, marginBottom: 20 }}>
        <Card>
          <CardHeader>
            <CardTitle style={{ fontSize: 13 }}>Visit activity this week</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <ComposedChart data={weeklyVisits}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="right" orientation="right" domain={[50, 110]} tickFormatter={(v: number) => `${v}%`} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar yAxisId="left" dataKey="visits" fill="#16a34a" radius={[4, 4, 0, 0]} name="Visits" />
                <Line yAxisId="right" type="monotone" dataKey="conversion" stroke="#d97706" strokeWidth={2} dot={{ r: 3 }} name="Conv. %" />
              </ComposedChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle style={{ fontSize: 13 }}>Revenue by product — this month</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={productRevenue} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" horizontal={false} />
                <XAxis type="number" tickFormatter={(v: number) => `₹${v / 1000}k`} tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="product" width={90} tick={{ fontSize: 10 }} />
                <Tooltip formatter={(v: number) => `₹${v.toLocaleString('en-IN')}`} />
                <Bar dataKey="revenue" fill="#16a34a" radius={[0, 4, 4, 0]} name="Revenue" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Recent visit log</CardTitle></CardHeader>
        <CardContent style={{ padding: 0 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr>
                {['Date', 'Customer', 'Tehsil', 'Visit type', 'Product pitched'].map(h => (
                  <th key={h} style={{ textAlign: 'left', padding: '10px 14px', fontSize: 11, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', borderBottom: '1px solid var(--border)' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visitLog.map((v, i) => (
                <tr key={i} style={{ background: i % 2 === 1 ? '#f9fafb' : 'white' }}>
                  <td style={{ padding: '10px 14px', color: '#6b7280' }}>{v.date}</td>
                  <td style={{ padding: '10px 14px', fontWeight: 500 }}>{v.customer}</td>
                  <td style={{ padding: '10px 14px', color: '#6b7280' }}>{v.tehsil}</td>
                  <td style={{ padding: '10px 14px' }}>
                    <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 9999, background: v.type === 'campaign_conducted' ? '#fef3c7' : '#f0fdf4', color: v.type === 'campaign_conducted' ? '#d97706' : '#16a34a' }}>
                      {v.type === 'retailer meeting' ? 'Retailer' : v.type === 'grower meeting' ? 'Grower' : 'Campaign'}
                    </span>
                  </td>
                  <td style={{ padding: '10px 14px' }}>{v.product}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  )
}
