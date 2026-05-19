type BadgeVariant = 'HIGH' | 'MEDIUM' | 'LOW' | 'OK' | 'active' | 'idle' | 'offline' | 'resolved' | 'pest' | 'weather' | 'competitor' | 'demand'

const config: Record<string, { bg: string; color: string; label?: string }> = {
  HIGH:       { bg: '#fef2f2', color: '#dc2626' },
  MEDIUM:     { bg: '#fffbeb', color: '#d97706' },
  LOW:        { bg: '#f8fafc', color: '#64748b' },
  OK:         { bg: '#f0fdf4', color: '#16a34a' },
  active:     { bg: '#f0fdf4', color: '#16a34a', label: '● Active' },
  idle:       { bg: '#fffbeb', color: '#d97706', label: '● Idle' },
  offline:    { bg: '#f8fafc', color: '#94a3b8', label: '● Offline' },
  resolved:   { bg: '#f0fdf4', color: '#16a34a' },
  pest:       { bg: '#fef2f2', color: '#dc2626' },
  weather:    { bg: '#eff6ff', color: '#3b82f6' },
  competitor: { bg: '#faf5ff', color: '#9333ea' },
  demand:     { bg: '#f0fdf4', color: '#16a34a' },
}

interface BadgeProps {
  level: string
  dot?: boolean
}

export function Badge({ level, dot }: BadgeProps) {
  const c = config[level] ?? config.LOW
  return (
    <span style={{
      background: c.bg, color: c.color,
      padding: '2px 8px', borderRadius: 9999,
      fontSize: 11, fontWeight: 600,
      display: 'inline-flex', alignItems: 'center', gap: 4,
      letterSpacing: '0.02em',
    }}>
      {dot && <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'currentColor', display: 'inline-block' }} />}
      {c.label ?? level}
    </span>
  )
}
