import { ReactNode } from 'react'

interface KPICardProps {
  label: string
  value: string | number
  delta?: string
  deltaType?: 'up' | 'down' | 'neutral'
  icon?: ReactNode
}

export function KPICard({ label, value, delta, deltaType = 'neutral', icon }: KPICardProps) {
  const deltaColor = deltaType === 'up' ? '#16a34a' : deltaType === 'down' ? '#ef4444' : '#64748b'
  const deltaPrefix = deltaType === 'up' ? '↑' : deltaType === 'down' ? '↓' : ''

  return (
    <div style={{
      background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8,
      padding: '18px 20px', boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
        <div style={{ fontSize: 13, color: '#64748b', fontWeight: 500 }}>{label}</div>
        {icon && <div style={{ color: '#94a3b8' }}>{icon}</div>}
      </div>
      <div style={{ fontSize: 26, fontWeight: 700, color: '#0f172a', marginBottom: 4 }}>{value}</div>
      {delta && (
        <div style={{ fontSize: 12, color: deltaColor, fontWeight: 500 }}>
          {deltaPrefix} {delta}
        </div>
      )}
    </div>
  )
}
