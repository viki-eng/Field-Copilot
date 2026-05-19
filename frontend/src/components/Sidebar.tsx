import { NavLink } from 'react-router-dom'
import { Map, Bell, BarChart2, TrendingUp, BookUser, Settings, Leaf, LogOut, X } from 'lucide-react'

const NAV = [
  { to: '/map',        icon: Map,        label: 'My Territory' },
  { to: '/alerts',     icon: Bell,       label: 'AI Briefing' },
  { to: '/analytics',  icon: BarChart2,  label: 'My Performance' },
  { to: '/forecast',   icon: TrendingUp, label: 'Market Signals' },
  { to: '/customers',  icon: BookUser,   label: 'My Customers' },
]

interface SidebarProps {
  isOpen?: boolean
  onClose?: () => void
  isMobileMode?: boolean
}

export function Sidebar({ isOpen = true, onClose, isMobileMode = false }: SidebarProps) {
  const sidebarStyle: React.CSSProperties = {
    width: 'var(--sidebar-width)',
    minWidth: 'var(--sidebar-width)',
    background: 'var(--sidebar-bg)',
    borderRight: '1px solid var(--sidebar-border)',
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    overflow: 'hidden',
    flexShrink: 0,
    ...(isMobileMode ? {
      position: 'fixed',
      top: 0,
      left: 0,
      zIndex: 200,
      transform: isOpen ? 'translateX(0)' : 'translateX(-100%)',
      transition: 'transform 0.25s ease',
      boxShadow: isOpen ? '0 0 40px rgba(0,0,0,0.15)' : 'none',
    } : {}),
  }

  return (
    <>
      {/* Mobile overlay backdrop */}
      {isMobileMode && isOpen && (
        <div
          onClick={onClose}
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)',
            zIndex: 199, backdropFilter: 'blur(2px)',
          }}
        />
      )}

      <aside style={sidebarStyle}>
        {/* Logo */}
        <div style={{ padding: '16px 16px 14px', borderBottom: '1px solid var(--sidebar-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 32, height: 32, background: '#f0fdf4',
              borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center',
              border: '1px solid #bbf7d0',
            }}>
              <Leaf size={16} color="#16a34a" />
            </div>
            <div>
              <div style={{ color: '#0f172a', fontSize: 14, fontWeight: 700, letterSpacing: '-0.01em' }}>FieldForce AI</div>
              <div style={{ color: '#16a34a', fontSize: 11, fontWeight: 500 }}>by Syngenta</div>
            </div>
          </div>
          {isMobileMode && (
            <button
              onClick={onClose}
              style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', padding: 4, borderRadius: 6, display: 'flex', alignItems: 'center' }}
            >
              <X size={16} />
            </button>
          )}
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, padding: '10px 8px', overflow: 'auto' }}>
          <div style={{ fontSize: 10, fontWeight: 600, color: '#94a3b8', letterSpacing: '0.08em', textTransform: 'uppercase', padding: '6px 8px 6px' }}>
            Navigation
          </div>
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} onClick={isMobileMode ? onClose : undefined} style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '8px 10px', borderRadius: 6,
              color: isActive ? '#16a34a' : '#475569',
              background: isActive ? '#f0fdf4' : 'transparent',
              fontWeight: isActive ? 600 : 400,
              fontSize: 13.5, textDecoration: 'none',
              marginBottom: 2, transition: 'all 0.15s',
              border: `1px solid ${isActive ? '#bbf7d0' : 'transparent'}`,
            })}>
              <Icon size={16} style={{ flexShrink: 0 }} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Settings */}
        <div style={{ padding: '0 8px 8px' }}>
          <NavLink to="/settings" onClick={isMobileMode ? onClose : undefined} style={({ isActive }) => ({
            display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px', borderRadius: 6,
            color: isActive ? '#16a34a' : '#475569',
            background: isActive ? '#f0fdf4' : 'transparent',
            fontWeight: 400, fontSize: 13.5, textDecoration: 'none', marginBottom: 2,
            border: `1px solid ${isActive ? '#bbf7d0' : 'transparent'}`,
          })}>
            <Settings size={16} />
            <span>Settings</span>
          </NavLink>
        </div>

        {/* User */}
        <div style={{ padding: '12px', borderTop: '1px solid var(--sidebar-border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 34, height: 34, background: 'linear-gradient(135deg,#16a34a,#15803d)',
              borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'white', fontSize: 12, fontWeight: 700, flexShrink: 0,
            }}>AS</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ color: '#0f172a', fontSize: 13, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>Arjun Sharma</div>
              <div style={{ color: '#64748b', fontSize: 11 }}>Sales Representative</div>
            </div>
            <button style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: 4, borderRadius: 4 }} title="Logout">
              <LogOut size={14} />
            </button>
          </div>
        </div>
      </aside>
    </>
  )
}
