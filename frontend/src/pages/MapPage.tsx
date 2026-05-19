import { useEffect, useState } from 'react'
import Map, { Marker, NavigationControl, Popup } from 'react-map-gl/mapbox'
import 'mapbox-gl/dist/mapbox-gl.css'
import { retailers, growers } from '../mockData'
import { Badge } from '../components/Badge'
import { ProgressBar } from '../components/ProgressBar'
import { Button } from '../components/Button'
import { X, FileText, MessageCircle, CheckCircle } from 'lucide-react'

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN as string

const PRIORITY_COLOR = { HIGH: '#dc2626', MEDIUM: '#d97706', LOW: '#16a34a' }

type RetailerItem = typeof retailers[0]
type GrowerItem = typeof growers[0]
type CustomerItem = RetailerItem | GrowerItem

interface MapPageProps { showToast: (msg: string) => void; viewMode: 'desktop' | 'mobile' }

export function MapPage({ showToast, viewMode }: MapPageProps) {
  const [typeFilter, setTypeFilter] = useState<'all' | 'retailer' | 'grower'>('all')
  const [selected, setSelected] = useState<CustomerItem | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [routeOpen, setRouteOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [popup, setPopup] = useState<CustomerItem | null>(null)

  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 800)
    return () => clearTimeout(t)
  }, [])

  const allItems: CustomerItem[] = [...retailers, ...growers]
  const outlets: CustomerItem[] = typeFilter === 'all' ? allItems
    : typeFilter === 'retailer' ? retailers
    : growers

  const openDrawer = (o: CustomerItem) => { setSelected(o); setDrawerOpen(true); setPopup(null) }

  const noToken = !MAPBOX_TOKEN || MAPBOX_TOKEN === 'your_token_here'

  return (
    <div style={{ display: 'flex', flexDirection: viewMode === 'mobile' ? 'column' : 'row', height: '100%', overflow: 'hidden' }}>
      {/* Left panel — desktop: left side | mobile: bottom strip */}
      <div style={{
        width: viewMode === 'mobile' ? '100%' : 300,
        minWidth: viewMode === 'mobile' ? 'auto' : 300,
        height: viewMode === 'mobile' ? 240 : 'auto',
        borderRight: viewMode === 'mobile' ? 'none' : '1px solid var(--border)',
        borderTop: viewMode === 'mobile' ? '1px solid var(--border)' : 'none',
        background: 'white', display: 'flex', flexDirection: 'column',
        overflow: 'hidden', order: viewMode === 'mobile' ? 2 : 1, flexShrink: 0,
      }}>
        <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--border)', fontWeight: 600 }}>
          Today's Visits — Ludhiana East
        </div>

        <div style={{ margin: 12, background: '#fee2e2', border: '1px solid #fecaca', borderRadius: 6, padding: '10px 12px', fontSize: 12 }}>
          <div style={{ fontWeight: 600, color: '#991b1b', marginBottom: 2 }}>⚠ 3 active alerts in your territory</div>
          <div style={{ color: '#b91c1c' }}>Pest outbreak · Weather deviation · Demand spike</div>
        </div>

        {/* Filter pills */}
        <div style={{ padding: '8px 12px', borderBottom: '1px solid var(--border)', display: 'flex', gap: 6 }}>
          {(['all', 'retailer', 'grower'] as const).map(f => (
            <Button
              key={f}
              size="sm"
              variant={typeFilter === f ? 'default' : 'outline'}
              onClick={() => setTypeFilter(f)}
            >
              {f === 'all' ? 'All' : f === 'retailer' ? 'Retailers' : 'Growers'}
            </Button>
          ))}
        </div>

        {/* Outlet list */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '8px 12px' }}>
          {loading ? (
            Array(4).fill(0).map((_, i) => (
              <div key={i} style={{ border: '1px solid var(--border)', borderRadius: 6, padding: 12, marginBottom: 8 }}>
                {[70, 50, 40].map(w => (
                  <div key={w} style={{ height: 12, width: `${w}%`, background: '#e5e7eb', borderRadius: 4, marginBottom: 6 }} />
                ))}
              </div>
            ))
          ) : outlets.map(o => {
            const isRetailer = o.type === 'retailer'
            return (
              <div key={o.id}
                onClick={() => openDrawer(o)}
                style={{
                  border: `1px solid ${selected?.id === o.id ? '#16a34a' : 'var(--border)'}`,
                  background: selected?.id === o.id ? '#f0fdf4' : 'white',
                  borderRadius: 6, padding: 12, marginBottom: 8, cursor: 'pointer',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
                  <span style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: PRIORITY_COLOR[o.priority_level], display: 'inline-block', flexShrink: 0 }} />
                    {o.name}
                  </span>
                  <Badge level={o.priority_level} />
                </div>
                <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 4 }}>
                  {isRetailer ? 'Retailer' : 'Grower'} · Last visit: {o.last_visit_days_ago} days ago
                </div>
                {'crop_stage' in o && o.crop_stage && (
                  <div style={{ fontSize: 11, color: '#d97706', marginTop: 2 }}>
                    🌾 {'crop' in o && o.crop ? o.crop.charAt(0).toUpperCase() + o.crop.slice(1) : ''} · {o.crop_stage}
                  </div>
                )}
                {'inventory' in o && o.inventory.some(i => i.status === 'critical') && (
                  <div style={{ fontSize: 11, color: '#dc2626', marginTop: 2 }}>⚠ Critically low stock</div>
                )}
                <div style={{ fontSize: 12, marginTop: 4 }}>Priority score: {o.priority_score}/100</div>
              </div>
            )
          })}
        </div>

        <div style={{ padding: 12, borderTop: '1px solid var(--border)' }}>
          <Button variant="default" style={{ width: '100%' }} onClick={() => setRouteOpen(true)}>
            My route for today
          </Button>
        </div>
      </div>

      {/* Map area */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden', order: viewMode === 'mobile' ? 1 : 2, minHeight: viewMode === 'mobile' ? 0 : 'auto' }}>
        {noToken ? (
          <div style={{ width: '100%', height: '100%', background: '#e8f4e8', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 12 }}>
            <div style={{ background: 'rgba(0,0,0,0.7)', color: 'white', padding: '10px 20px', borderRadius: 8, fontSize: 13 }}>
              Add your Mapbox token to <code>frontend/.env</code> → <code>VITE_MAPBOX_TOKEN=pk.xxx</code>
            </div>
          </div>
        ) : (
          <Map
            mapboxAccessToken={MAPBOX_TOKEN}
            initialViewState={{ longitude: 75.85, latitude: 30.92, zoom: 10 }}
            style={{ width: '100%', height: '100%' }}
            mapStyle="mapbox://styles/mapbox/streets-v12"
            onClick={() => setPopup(null)}
          >
            <NavigationControl position="bottom-right" />

            {/* Customer markers */}
            {outlets.map(o => (
              <Marker key={o.id} longitude={o.lng} latitude={o.lat} anchor="center">
                <div
                  onClick={(e) => { e.stopPropagation(); setPopup(o) }}
                  title={o.name}
                  style={{
                    width: o.type === 'retailer' ? 16 : 14,
                    height: o.type === 'retailer' ? 16 : 14,
                    background: PRIORITY_COLOR[o.priority_level],
                    borderRadius: o.type === 'retailer' ? 3 : '50%',
                    border: '2px solid white',
                    cursor: 'pointer',
                    boxShadow: '0 1px 4px rgba(0,0,0,0.3)',
                    transition: 'transform 0.15s',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.transform = 'scale(1.5)')}
                  onMouseLeave={e => (e.currentTarget.style.transform = 'scale(1)')}
                />
              </Marker>
            ))}

            {/* Customer popup on marker click */}
            {popup && (
              <Popup
                longitude={popup.lng}
                latitude={popup.lat}
                anchor="bottom"
                onClose={() => setPopup(null)}
                closeOnClick={false}
                offset={10}
              >
                <div style={{ padding: '4px 2px', minWidth: 180 }}>
                  <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4 }}>{popup.name}</div>
                  <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 6 }}>
                    {popup.type === 'retailer' ? 'Retailer' : 'Grower'} · {popup.last_visit_days_ago}d ago
                  </div>
                  <div style={{ marginBottom: 8 }}><Badge level={popup.priority_level} /></div>
                  <Button
                    variant="default"
                    size="sm"
                    style={{ width: '100%' }}
                    onClick={() => openDrawer(popup)}
                  >
                    View details →
                  </Button>
                </div>
              </Popup>
            )}
          </Map>
        )}
      </div>

      {/* Customer detail drawer */}
      {drawerOpen && selected && (
        <>
          <div onClick={() => setDrawerOpen(false)} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.3)', zIndex: 100 }} />
          <div style={{
            position: 'fixed', top: 0, right: 0, width: 380, height: '100%',
            background: 'white', borderLeft: '1px solid var(--border)',
            zIndex: 101, overflowY: 'auto',
            animation: 'slideRight 0.3s ease',
          }}>
            <style>{`@keyframes slideRight { from { transform: translateX(100%); } to { transform: translateX(0); } }`}</style>

            <div style={{ padding: 20, borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: 15 }}>{selected.name}</div>
                <div style={{ fontSize: 12, color: '#6b7280' }}>
                  {selected.type === 'retailer'
                    ? `Retailer · ${selected.tehsil}`
                    : `Grower · ${'crop' in selected && selected.crop ? selected.crop : 'No crop'} · ${'crop_stage' in selected ? selected.crop_stage : ''}`
                  }
                </div>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setDrawerOpen(false)}>
                <X size={16} />
              </Button>
            </div>

            <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)' }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 10 }}>Priority Score</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ flex: 1 }}><ProgressBar pct={selected.priority_score} height={8} /></div>
                <span style={{ fontWeight: 600 }}>{selected.priority_score}/100</span>
                <Badge level={selected.priority_level} />
              </div>
            </div>

            <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)' }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 12 }}>Context</div>
              {selected.type === 'retailer' && 'inventory' in selected ? (
                <div>
                  {selected.inventory.map(inv => (
                    <div key={inv.sku} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 13 }}>
                      <span style={{ color: '#6b7280' }}>{inv.sku}</span>
                      <span style={{ color: inv.status === 'critical' ? '#dc2626' : inv.status === 'low' ? '#d97706' : '#374151', fontWeight: 500 }}>
                        {inv.qty} units {inv.status === 'critical' ? '🔴' : inv.status === 'low' ? '🟡' : ''}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div>
                  {(selected.type === 'grower' && 'crop' in selected) ? (
                    [
                      ['Crop', `${selected.crop ?? 'Unknown'}`],
                      ['Stage', 'crop_stage' in selected ? (selected.crop_stage ?? '—') : '—'],
                      ['Farm size', `${'farm_size_acres' in selected ? selected.farm_size_acres : '—'} acres`],
                      ['Last visit', `${selected.last_visit_days_ago} days ago`],
                      ['Campaign', 'campaign_attended' in selected ? (selected.campaign_attended ? '✓ Attended' : 'Not attended') : '—'],
                      ['Product scanned', 'product_name' in selected ? (selected.product_name ?? 'None') : 'None'],
                    ].map(([label, val]) => (
                      <div key={String(label)} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: 13 }}>
                        <span style={{ color: '#6b7280' }}>{label}</span>
                        <span>{val}</span>
                      </div>
                    ))
                  ) : null}
                </div>
              )}
            </div>

            <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)' }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 10 }}>AI Recommendation</div>
              <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 6, padding: 12, fontSize: 13, color: '#166534', marginBottom: 10 }}>
                {selected.ai_recommendation}
              </div>
              <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 6 }}>Talking points:</div>
              <ul style={{ paddingLeft: 16 }}>
                {selected.talking_points.map(p => (
                  <li key={p} style={{ fontSize: 12, color: '#6b7280', marginBottom: 4 }}>{p}</li>
                ))}
              </ul>
            </div>

            <div style={{ padding: 16, display: 'flex', gap: 8 }}>
              {selected.type === 'grower' && (
                <Button variant="outline" style={{ flex: 1 }} onClick={() => showToast('✓ WhatsApp message sent')}>
                  <MessageCircle size={14} style={{ marginRight: 4 }} /> WhatsApp
                </Button>
              )}
              <Button variant="default" style={{ flex: 1 }} onClick={() => showToast('✓ Visit logged successfully')}>
                <CheckCircle size={14} style={{ marginRight: 4 }} /> Log visit
              </Button>
            </div>
          </div>
        </>
      )}

      {/* Route modal */}
      {routeOpen && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: 'white', borderRadius: 10, width: 520, maxHeight: '85vh', overflowY: 'auto' }}>
            <div style={{ padding: 20, borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: 15 }}>My route for today</div>
                <div style={{ fontSize: 12, color: '#6b7280' }}>Ludhiana East · 6 stops · ~62 km</div>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setRouteOpen(false)}>
                <X size={16} />
              </Button>
            </div>
            <div style={{ padding: 20 }}>
              {[
                { n: 1, color: '#dc2626', name: 'Ramesh Agro Store', time: '9:00am', note: 'Vertimec critically low — urgent restock' },
                { n: 2, color: '#dc2626', name: 'Paramjit Singh (Grower)', time: '10:30am', note: 'Wheat at tillering — fungicide pitch now' },
                { n: 3, color: '#dc2626', name: 'Gurpreet Agro Traders', time: '12:00pm', note: 'Overdue visit — 12 days. High-value account' },
                { n: 4, color: '#d97706', name: 'Karamjit Kaur (Grower)', time: '2:00pm', note: 'Product scan signal — Amistar 250 SC' },
                { n: 5, color: '#d97706', name: 'Punjab Krishi Centre', time: '3:30pm', note: 'Introduce Axial 50 EC — competitor gap' },
                { n: 6, color: '#d97706', name: 'Balwant Seed House', time: '4:45pm', note: 'Campaign follow-up — order conversion' },
              ].map(s => (
                <div key={s.n} style={{ display: 'flex', gap: 12, padding: '12px 0', borderBottom: '1px solid #f3f4f6', alignItems: 'flex-start' }}>
                  <div style={{ width: 24, height: 24, background: '#16a34a', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: 11, fontWeight: 600, flexShrink: 0 }}>{s.n}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ fontWeight: 500 }}><span style={{ color: s.color }}>●</span> {s.name}</span>
                      <span style={{ fontSize: 12, color: '#6b7280' }}>{s.time}</span>
                    </div>
                    <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>{s.note}</div>
                  </div>
                </div>
              ))}
            </div>
            <div style={{ padding: 16, borderTop: '1px solid var(--border)', display: 'flex', gap: 8 }}>
              <Button variant="default" onClick={() => { showToast('✓ Route saved to phone'); setRouteOpen(false) }}>
                Save to phone
              </Button>
              <Button variant="outline" onClick={() => showToast('✓ PDF exported')}>
                <FileText size={14} /> Export PDF
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
