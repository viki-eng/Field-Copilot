import { useLocation } from 'react-router-dom'
import { Search, Bell, RefreshCw, Calendar, Monitor, Smartphone, Menu } from 'lucide-react'
import { Button } from './Button'
import { retailers, growers } from '../mockData'

const PAGE_TITLES: Record<string, { title: string; sub: string }> = {
  '/map':       { title: 'My Territory',    sub: "Ludhiana East · Today's visit list" },
  '/alerts':    { title: 'AI Briefing',     sub: 'What your AI assistant flagged today' },
  '/analytics': { title: 'My Performance', sub: 'Ludhiana East · Current month' },
  '/forecast':  { title: 'Market Signals', sub: 'Demand forecast for your territory' },
  '/customers': { title: 'My Customers',   sub: `${retailers.length} retailers · ${growers.length} growers` },
}

interface TopbarProps {
  alertCount: number
  onSync: () => void
  viewMode: 'desktop' | 'mobile'
  onToggleView: () => void
  onMenuOpen: () => void
}

export function Topbar({ alertCount, onSync, viewMode, onToggleView, onMenuOpen }: TopbarProps) {
  const { pathname } = useLocation()
  const page = PAGE_TITLES[pathname] ?? { title: 'FieldForce AI', sub: '' }
  const today = new Date().toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' })

  return (
    <header style={{
      height: 'var(--topbar-height)', background: '#fff',
      borderBottom: '1px solid #e2e8f0',
      display: 'flex', alignItems: 'center',
      padding: '0 16px', gap: 10, flexShrink: 0,
    }}>
      {/* Hamburger — shown in mobile mode */}
      {viewMode === 'mobile' && (
        <button
          onClick={onMenuOpen}
          style={{
            background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8,
            width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'pointer', color: '#64748b', flexShrink: 0,
          }}
        >
          <Menu size={16} />
        </button>
      )}

      {/* Title */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 15, fontWeight: 700, color: '#0f172a', letterSpacing: '-0.01em', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{page.title}</div>
        {page.sub && <div style={{ fontSize: 11, color: '#94a3b8', fontWeight: 400 }}>{page.sub}</div>}
      </div>

      {/* Search — hide on mobile mode */}
      {viewMode === 'desktop' && (
        <div style={{ position: 'relative' }}>
          <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
          <input
            type="text"
            placeholder="Search customers, tehsils..."
            style={{
              border: '1px solid #e2e8f0', borderRadius: 8,
              padding: '7px 12px 7px 32px', width: 220, outline: 'none',
              fontSize: 13, color: '#0f172a', background: '#f8fafc',
              transition: 'border-color 0.15s',
            }}
            onFocus={e => (e.target.style.borderColor = '#16a34a')}
            onBlur={e => (e.target.style.borderColor = '#e2e8f0')}
          />
        </div>
      )}

      {/* Bell */}
      <button style={{
        position: 'relative', background: '#f8fafc', border: '1px solid #e2e8f0',
        borderRadius: 8, width: 36, height: 36, display: 'flex', alignItems: 'center',
        justifyContent: 'center', cursor: 'pointer', color: '#64748b', flexShrink: 0,
      }}>
        <Bell size={15} />
        {alertCount > 0 && (
          <span style={{
            position: 'absolute', top: -4, right: -4,
            background: '#ef4444', color: 'white', borderRadius: 9999,
            fontSize: 10, padding: '1px 5px', fontWeight: 700,
            border: '2px solid white', lineHeight: 1.4,
          }}>{alertCount}</span>
        )}
      </button>

      {/* Date — hide on mobile mode */}
      {viewMode === 'desktop' && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 6,
          background: '#f8fafc', border: '1px solid #e2e8f0',
          borderRadius: 8, padding: '7px 10px', fontSize: 12, color: '#64748b', flexShrink: 0,
        }}>
          <Calendar size={13} />
          {today}
        </div>
      )}

      {/* View mode toggle */}
      <button
        onClick={onToggleView}
        title={viewMode === 'desktop' ? 'Switch to mobile view' : 'Switch to desktop view'}
        style={{
          background: viewMode === 'mobile' ? '#f0fdf4' : '#f8fafc',
          border: `1px solid ${viewMode === 'mobile' ? '#bbf7d0' : '#e2e8f0'}`,
          borderRadius: 8, width: 36, height: 36,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: 'pointer',
          color: viewMode === 'mobile' ? '#16a34a' : '#64748b',
          flexShrink: 0,
          transition: 'all 0.15s',
        }}
      >
        {viewMode === 'desktop' ? <Smartphone size={15} /> : <Monitor size={15} />}
      </button>

      {/* Sync */}
      <Button variant="default" size="sm" onClick={onSync} style={{ gap: 6, flexShrink: 0 }}>
        <RefreshCw size={13} />
        {viewMode === 'desktop' ? 'Sync data' : ''}
      </Button>
    </header>
  )
}
