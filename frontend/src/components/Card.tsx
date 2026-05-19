import { HTMLAttributes } from 'react'

export function Card({ style, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div style={{
      background: '#fff', border: '1px solid #e2e8f0',
      borderRadius: 8, boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
      ...style,
    }} {...props} />
  )
}

export function CardHeader({ style, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div style={{ padding: '16px 20px', borderBottom: '1px solid #e2e8f0', ...style }} {...props} />
}

export function CardTitle({ style, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div style={{ fontSize: 15, fontWeight: 600, color: '#0f172a', ...style }} {...props} />
}

export function CardContent({ style, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div style={{ padding: '16px 20px', ...style }} {...props} />
}
