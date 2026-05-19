import { ButtonHTMLAttributes, forwardRef } from 'react'

type Variant = 'default' | 'secondary' | 'outline' | 'ghost' | 'destructive'
type Size = 'sm' | 'md' | 'lg' | 'icon'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
}

const base: React.CSSProperties = {
  display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
  gap: 6, fontWeight: 500, borderRadius: 6, border: 'none',
  transition: 'all 0.15s', whiteSpace: 'nowrap', cursor: 'pointer',
  fontFamily: 'inherit',
}

const variants: Record<Variant, React.CSSProperties> = {
  default: { background: '#16a34a', color: '#fff' },
  secondary: { background: '#f1f5f9', color: '#0f172a' },
  outline: { background: 'transparent', color: '#0f172a', border: '1px solid #e2e8f0' },
  ghost: { background: 'transparent', color: '#0f172a' },
  destructive: { background: '#ef4444', color: '#fff' },
}

const sizes: Record<Size, React.CSSProperties> = {
  sm: { fontSize: 12, padding: '5px 10px', height: 32 },
  md: { fontSize: 14, padding: '7px 14px', height: 38 },
  lg: { fontSize: 14, padding: '9px 18px', height: 42 },
  icon: { width: 36, height: 36, padding: 0 },
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'default', size = 'md', style, ...props }, ref) => (
    <button
      ref={ref}
      style={{ ...base, ...variants[variant], ...sizes[size], ...style }}
      onMouseEnter={e => {
        const el = e.currentTarget
        if (variant === 'default') el.style.background = '#15803d'
        else if (variant === 'secondary') el.style.background = '#e2e8f0'
        else if (variant === 'outline' || variant === 'ghost') el.style.background = '#f1f5f9'
        else if (variant === 'destructive') el.style.background = '#dc2626'
      }}
      onMouseLeave={e => {
        const el = e.currentTarget
        Object.assign(el.style, variants[variant])
      }}
      {...props}
    />
  )
)
Button.displayName = 'Button'
