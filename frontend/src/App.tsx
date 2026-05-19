import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Sidebar } from './components/Sidebar'
import { Topbar } from './components/Topbar'
import { Toast } from './components/Toast'
import { MapPage } from './pages/MapPage'
import { AlertsPage } from './pages/AlertsPage'
import { AnalyticsPage } from './pages/AnalyticsPage'
import { ForecastPage } from './pages/ForecastPage'
import { CustomersPage } from './pages/CustomersPage'

const MOBILE_BP = 768

export default function App() {
  const [toast, setToast] = useState('')
  const [alertCount, setAlertCount] = useState(4)
  const [viewMode, setViewMode] = useState<'desktop' | 'mobile'>(
    window.innerWidth <= MOBILE_BP ? 'mobile' : 'desktop'
  )
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    const mq = window.matchMedia(`(max-width: ${MOBILE_BP}px)`)
    const handler = (e: MediaQueryListEvent) => {
      setViewMode(e.matches ? 'mobile' : 'desktop')
      if (!e.matches) setSidebarOpen(false)
    }
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])

  const showToast = (msg: string) => setToast(msg)
  const toggleView = () => {
    setViewMode(v => v === 'desktop' ? 'mobile' : 'desktop')
    setSidebarOpen(false)
  }

  const isMobile = viewMode === 'mobile'

  return (
    <BrowserRouter>
      <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', position: 'relative' }}>
        <Sidebar
          isOpen={isMobile ? sidebarOpen : true}
          onClose={() => setSidebarOpen(false)}
          isMobileMode={isMobile}
        />
        <div style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          minWidth: 0,
          marginLeft: isMobile ? 0 : undefined,
        }}>
          <Topbar
            alertCount={alertCount}
            onSync={() => showToast('✓ Data synced')}
            viewMode={viewMode}
            onToggleView={toggleView}
            onMenuOpen={() => setSidebarOpen(true)}
          />
          <main style={{ flex: 1, overflow: 'hidden' }}>
            <Routes>
              <Route path="/" element={<Navigate to="/map" replace />} />
              <Route path="/map" element={<MapPage showToast={showToast} viewMode={viewMode} />} />
              <Route path="/alerts" element={<AlertsPage showToast={showToast} onAlertCountChange={setAlertCount} viewMode={viewMode} />} />
              <Route path="/analytics" element={<AnalyticsPage viewMode={viewMode} />} />
              <Route path="/forecast" element={<ForecastPage viewMode={viewMode} />} />
              <Route path="/customers" element={<CustomersPage showToast={showToast} viewMode={viewMode} />} />
            </Routes>
          </main>
        </div>
      </div>
      {toast && <Toast message={toast} onDismiss={() => setToast('')} />}
    </BrowserRouter>
  )
}
