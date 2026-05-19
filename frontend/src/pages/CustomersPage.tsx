import { useState } from 'react'
import { retailers, growers } from '../mockData'
import { Badge } from '../components/Badge'
import { Button } from '../components/Button'
import { Card, CardContent } from '../components/Card'
import { Search, MapPin, Wheat, Store, Phone, CheckCircle, SlidersHorizontal } from 'lucide-react'

type RetailerItem = typeof retailers[0]
type GrowerItem = typeof growers[0]
type Customer = RetailerItem | GrowerItem

interface CustomersPageProps {
  showToast: (msg: string) => void
  viewMode: 'desktop' | 'mobile'
}

export function CustomersPage({ showToast, viewMode }: CustomersPageProps) {
  const [tab, setTab] = useState<'all' | 'retailer' | 'grower'>('all')
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<Customer | null>(null)

  const all: Customer[] = [...retailers, ...growers]
  const filtered = all
    .filter(c => tab === 'all' || c.type === tab)
    .filter(c => search === '' || c.name.toLowerCase().includes(search.toLowerCase()) || c.tehsil.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => b.priority_score - a.priority_score)

  const retailerCount = retailers.length
  const growerCount = growers.length

  return (
    <div style={{ height: '100%', display: 'flex', overflow: 'hidden' }}>
      {/* Left: customer list */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 20, minWidth: 0 }}>
        {/* Header stats */}
        <div style={{ display: 'grid', gridTemplateColumns: viewMode === 'mobile' ? '1fr 1fr' : 'repeat(3, 1fr)', gap: 12, marginBottom: 20 }}>
          {[
            { label: 'Total customers', value: all.length, icon: <SlidersHorizontal size={16} color="#16a34a" /> },
            { label: 'Retailers', value: retailerCount, icon: <Store size={16} color="#3b82f6" /> },
            { label: 'Growers', value: growerCount, icon: <Wheat size={16} color="#d97706" /> },
          ].map(stat => (
            <Card key={stat.label}>
              <CardContent style={{ padding: '14px 16px', display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ width: 36, height: 36, background: '#f8fafc', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid var(--border)' }}>
                  {stat.icon}
                </div>
                <div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: '#0f172a' }}>{stat.value}</div>
                  <div style={{ fontSize: 11, color: '#64748b' }}>{stat.label}</div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
          {([['all', 'All'], ['retailer', 'Retailers'], ['grower', 'Growers']] as const).map(([val, label]) => (
            <Button key={val} variant={tab === val ? 'default' : 'outline'} size="sm" onClick={() => setTab(val)}>
              {label}
            </Button>
          ))}
          <div style={{ position: 'relative', marginLeft: 'auto' }}>
            <Search size={13} style={{ position: 'absolute', left: 9, top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search customers..."
              style={{ border: '1px solid var(--border)', borderRadius: 8, padding: '7px 10px 7px 28px', fontSize: 13, outline: 'none', width: 200, background: '#f8fafc' }}
            />
          </div>
        </div>

        {/* Customer list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {filtered.map(c => {
            const isRetailer = c.type === 'retailer'
            const isSelected = selected?.id === c.id
            return (
              <Card
                key={c.id}
                style={{
                  cursor: 'pointer',
                  border: isSelected ? '1px solid #16a34a' : undefined,
                  background: isSelected ? '#f0fdf4' : undefined,
                }}
                onClick={() => setSelected(isSelected ? null : c)}
              >
                <CardContent style={{ padding: '14px 16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
                    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', flex: 1, minWidth: 0 }}>
                      <div style={{
                        width: 36, height: 36, borderRadius: isRetailer ? 8 : '50%',
                        background: isRetailer ? '#dbeafe' : '#fef3c7',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        flexShrink: 0,
                      }}>
                        {isRetailer ? <Store size={16} color="#3b82f6" /> : <Wheat size={16} color="#d97706" />}
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontWeight: 600, fontSize: 14, color: '#0f172a', marginBottom: 2 }}>{c.name}</div>
                        <div style={{ fontSize: 12, color: '#64748b', display: 'flex', alignItems: 'center', gap: 4 }}>
                          <MapPin size={11} /> {c.tehsil} ·{' '}
                          {isRetailer ? 'Retailer' : `Grower · ${'crop' in c && c.crop ? c.crop : 'No crop'}`}
                        </div>
                        {'crop_stage' in c && c.crop_stage && (
                          <div style={{ fontSize: 11, color: '#d97706', marginTop: 3 }}>
                            🌾 {c.crop_stage}
                          </div>
                        )}
                        {'inventory' in c && c.inventory.some(i => i.status === 'critical') && (
                          <div style={{ fontSize: 11, color: '#dc2626', marginTop: 3 }}>
                            ⚠ Critically low stock
                          </div>
                        )}
                      </div>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4, flexShrink: 0 }}>
                      <Badge level={c.priority_level} />
                      <div style={{ fontSize: 11, color: '#94a3b8' }}>{c.last_visit_days_ago}d ago</div>
                    </div>
                  </div>

                  {/* Expanded detail on click */}
                  {isSelected && (
                    <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--border)' }}>
                      <div style={{ fontSize: 11, fontWeight: 600, color: '#16a34a', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>AI Recommendation</div>
                      <div style={{ fontSize: 13, color: '#374151', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 6, padding: '10px 12px', marginBottom: 12 }}>
                        {c.ai_recommendation}
                      </div>
                      {'inventory' in c && (
                        <div style={{ marginBottom: 12 }}>
                          <div style={{ fontSize: 11, fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', marginBottom: 6 }}>Inventory</div>
                          {c.inventory.map(inv => (
                            <div key={inv.sku} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                              <span style={{ color: '#374151' }}>{inv.sku}</span>
                              <span style={{ fontWeight: 600, color: inv.status === 'critical' ? '#dc2626' : inv.status === 'low' ? '#d97706' : '#16a34a' }}>
                                {inv.qty} units
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                      <div style={{ display: 'flex', gap: 8 }}>
                        <Button variant="default" size="sm" style={{ flex: 1 }} onClick={(e) => { e.stopPropagation(); showToast('✓ Visit logged') }}>
                          <CheckCircle size={13} style={{ marginRight: 4 }} /> Log visit
                        </Button>
                        {!isRetailer && (
                          <Button variant="outline" size="sm" style={{ flex: 1 }} onClick={(e) => { e.stopPropagation(); showToast('✓ WhatsApp sent') }}>
                            <Phone size={13} style={{ marginRight: 4 }} /> WhatsApp
                          </Button>
                        )}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      </div>
    </div>
  )
}
