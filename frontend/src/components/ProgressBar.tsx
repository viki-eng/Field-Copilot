interface ProgressBarProps {
  pct: number
  height?: number
  color?: string
}

export function ProgressBar({ pct, height = 6, color = '#16a34a' }: ProgressBarProps) {
  return (
    <div style={{ height, background: '#f1f5f9', borderRadius: 99, overflow: 'hidden' }}>
      <div style={{
        height: '100%', width: `${Math.min(Math.max(pct, 0), 100)}%`,
        background: color, borderRadius: 99, transition: 'width 0.4s ease',
      }} />
    </div>
  )
}
