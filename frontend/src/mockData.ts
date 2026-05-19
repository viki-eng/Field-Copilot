// Real data sourced from CSVs: retailers.csv, growers.csv, retailer_inventory_weekly.csv,
// retailer_visit_log.csv for REP_0018 / TER_0018 (Ludhiana East, Punjab)

// Tehsil → approximate lat/lng for Ludhiana district
export const TEHSIL_COORDS: Record<string, [number, number]> = {
  Ludhiana_T001: [30.95, 75.82],
  Ludhiana_T002: [30.90, 75.79],
  Ludhiana_T003: [30.86, 75.83],
  Ludhiana_T004: [30.93, 75.91],
  Ludhiana_T005: [30.87, 75.94],
  Ludhiana_T006: [30.98, 75.88],
  Ludhiana_T007: [30.83, 75.80],
  Ludhiana_T008: [30.97, 75.80],
  Ludhiana_T009: [30.85, 75.91],
  Ludhiana_T010: [30.91, 75.96],
  Ludhiana_T011: [30.94, 75.86],
  Ludhiana_T012: [30.89, 75.76],
}

// Rep profile (REP_0018)
export const MY_PROFILE = {
  id: 'REP_0018',
  name: 'Arjun Sharma',
  initials: 'AS',
  territory: 'Ludhiana East',
  territory_id: 'TER_0018',
  district: 'Ludhiana',
  state: 'Punjab',
  visits_today: 3,
  visits_target: 7,
  conversion_rate: 74,
  mtd_revenue: 324000,
  mtd_target: 450000,
  ai_adoption: 82,
  trend: 'up' as const,
}

// Retailers (from retailers.csv for TER_0018 + inventory from retailer_inventory_weekly.csv 2026-03-29)
export const retailers = [
  {
    id: 'RTL_00130', name: 'Ramesh Agro Store', type: 'retailer' as const,
    tehsil: 'Ludhiana_T011', district: 'Ludhiana',
    lat: 30.94, lng: 75.86,
    last_visit_days_ago: 8, last_visit_type: 'retailer meeting',
    priority_score: 91, priority_level: 'HIGH' as const,
    inventory: [
      { sku: 'Vertimec 1.8 EC', qty: 6, status: 'critical' as const },
      { sku: 'Movondo', qty: 20, status: 'ok' as const },
      { sku: 'Tilt 250 EC', qty: 106, status: 'ok' as const },
    ],
    last_order_value: 28400,
    ai_recommendation: 'Vertimec 1.8 EC critically low (6 units). Wheat tillering season — push Tilt 250 EC restock. High pest pressure in T011.',
    talking_points: ['Vertimec stock down 94% from last month', 'Wheat at tillering — fungicide window opening', '3 nearby growers have no product coverage'],
  },
  {
    id: 'RTL_00131', name: 'Punjab Krishi Centre', type: 'retailer' as const,
    tehsil: 'Ludhiana_T006', district: 'Ludhiana',
    lat: 30.98, lng: 75.88,
    last_visit_days_ago: 5, last_visit_type: 'retailer meeting',
    priority_score: 74, priority_level: 'MEDIUM' as const,
    inventory: [
      { sku: 'Vibrance Integral', qty: 24, status: 'ok' as const },
      { sku: 'Topik 15 WP', qty: 191, status: 'ok' as const },
    ],
    last_order_value: 19200,
    ai_recommendation: 'Introduce Axial 50 EC for wheat weed control — no stock currently. Competitor filling this gap.',
    talking_points: ['No herbicide for wheat in stock', 'Competitor Dhanuka has Axial equivalent', 'Q2 promotional pricing available now'],
  },
  {
    id: 'RTL_00132', name: 'Gurpreet Agro Traders', type: 'retailer' as const,
    tehsil: 'Ludhiana_T002', district: 'Ludhiana',
    lat: 30.90, lng: 75.79,
    last_visit_days_ago: 12, last_visit_type: 'retailer meeting',
    priority_score: 85, priority_level: 'HIGH' as const,
    inventory: [
      { sku: 'Vertimec 1.8 EC', qty: 26, status: 'ok' as const },
      { sku: 'Vibrance Integral', qty: 78, status: 'ok' as const },
    ],
    last_order_value: 31000,
    ai_recommendation: 'Overdue visit (12 days). Strong account — push Score 250 EC and Amistar 250 SC for wheat flag leaf season.',
    talking_points: ['Last visit 12 days ago — schedule overdue', 'Wheat approaching flag leaf — fungicide critical', 'High-volume account, retention priority'],
  },
  {
    id: 'RTL_00133', name: 'Balwant Seed House', type: 'retailer' as const,
    tehsil: 'Ludhiana_T009', district: 'Ludhiana',
    lat: 30.85, lng: 75.91,
    last_visit_days_ago: 3, last_visit_type: 'campaign_conducted',
    priority_score: 62, priority_level: 'MEDIUM' as const,
    inventory: [
      { sku: 'Amistar 250 SC', qty: 129, status: 'ok' as const },
      { sku: 'Topik 15 WP', qty: 172, status: 'ok' as const },
      { sku: 'Axial 50 EC', qty: 19, status: 'low' as const },
    ],
    last_order_value: 14800,
    ai_recommendation: 'Axial 50 EC running low (19 units). Recent campaign visit — follow up on order conversion.',
    talking_points: ['Axial 50 EC below reorder threshold', 'Campaign attendance was high — 8 growers registered', 'Follow up on Actara 25 WG interest from campaign'],
  },
  {
    id: 'RTL_00134', name: 'Sukhdev Farm Inputs', type: 'retailer' as const,
    tehsil: 'Ludhiana_T004', district: 'Ludhiana',
    lat: 30.93, lng: 75.91,
    last_visit_days_ago: 6, last_visit_type: 'retailer meeting',
    priority_score: 55, priority_level: 'LOW' as const,
    inventory: [
      { sku: 'Movondo', qty: 29, status: 'ok' as const },
      { sku: 'Axial 50 EC', qty: 60, status: 'ok' as const },
      { sku: 'Actara 25 WG', qty: 26, status: 'ok' as const },
    ],
    last_order_value: 11200,
    ai_recommendation: 'Routine visit. Introduce Vibrance Integral for upcoming Kharif seed treatment window.',
    talking_points: ['Kharif season prep begins next month', 'Vibrance Integral not in stock — opportunity', 'Actara 25 WG moving well — suggest reorder'],
  },
  {
    id: 'RTL_00135', name: 'Manpreet Agri Solutions', type: 'retailer' as const,
    tehsil: 'Ludhiana_T001', district: 'Ludhiana',
    lat: 30.95, lng: 75.82,
    last_visit_days_ago: 9, last_visit_type: 'retailer meeting',
    priority_score: 78, priority_level: 'HIGH' as const,
    inventory: [
      { sku: 'Vertimec 1.8 EC', qty: 134, status: 'ok' as const },
      { sku: 'Actara 25 WG', qty: 44, status: 'ok' as const },
      { sku: 'Alto 5 SC', qty: 132, status: 'ok' as const },
    ],
    last_order_value: 22600,
    ai_recommendation: 'Visit overdue. Alto 5 SC slow-moving — suggest push promotion. Introduce Tilt 250 EC (wheat season).',
    talking_points: ['9 days since last visit', 'Alto 5 SC overstocked — suggest promotion to growers', 'Tilt 250 EC absent from stock'],
  },
  {
    id: 'RTL_00136', name: 'Harpreet Kisan Store', type: 'retailer' as const,
    tehsil: 'Ludhiana_T001', district: 'Ludhiana',
    lat: 30.96, lng: 75.81,
    last_visit_days_ago: 2, last_visit_type: 'retailer meeting',
    priority_score: 48, priority_level: 'LOW' as const,
    inventory: [
      { sku: 'Amistar 250 SC', qty: 56, status: 'ok' as const },
      { sku: 'Score 250 EC', qty: 124, status: 'ok' as const },
      { sku: 'Actara 25 WG', qty: 65, status: 'ok' as const },
      { sku: 'Axial 50 EC', qty: 59, status: 'ok' as const },
    ],
    last_order_value: 9800,
    ai_recommendation: 'Well-stocked, recent visit. No immediate action — routine relationship maintenance.',
    talking_points: ['Good stock levels across SKUs', 'Ask about competitor activity in tehsil', 'Reminder on Syngenta loyalty program points'],
  },
]

// Growers (from growers.csv for Ludhiana district, tehsils T001-T012, with real crop data)
export const growers = [
  {
    id: 'GRW_00238', name: 'Paramjit Singh', type: 'grower' as const,
    tehsil: 'Ludhiana_T011', district: 'Ludhiana',
    lat: 30.94 + 0.01, lng: 75.87,
    age: 46, gender: 'male', language: 'Punjabi',
    farm_size_acres: 3.2, device: 'smartphone',
    crop: 'wheat', season: 'Rabi_2025-26',
    crop_stage: 'Tillering', crop_stage_date: '2026-01-15',
    harvest_start: '2026-03-20',
    product_scanned: false, product_name: null,
    campaign_attended: false,
    last_visit_days_ago: 14,
    priority_score: 88, priority_level: 'HIGH' as const,
    ai_recommendation: 'Wheat at tillering — critical fungicide window. Recommend Tilt 250 EC (500ml) application within 7 days. High pest pressure in T011.',
    talking_points: ['Wheat tillering stage — fungicide critical now', 'Grey leaf spot risk HIGH in T011', 'Farm size 3.2 acres — suggest 4 units Tilt 250 EC'],
  },
  {
    id: 'GRW_05117', name: 'Karamjit Kaur', type: 'grower' as const,
    tehsil: 'Ludhiana_T011', district: 'Ludhiana',
    lat: 30.93, lng: 75.85,
    age: 52, gender: 'female', language: 'Punjabi',
    farm_size_acres: 4.64, device: 'smartphone',
    crop: 'potato', season: 'Rabi_2025-26',
    crop_stage: 'Harvest (done)', crop_stage_date: '2026-03-10',
    harvest_start: '2026-01-20',
    product_scanned: true, product_name: 'Amistar 250 SC',
    campaign_attended: false,
    last_visit_days_ago: 21,
    priority_score: 79, priority_level: 'HIGH' as const,
    ai_recommendation: 'Scanned Amistar 250 SC — high intent signal. Potato harvest done; discuss next Kharif crop (rice/maize). Seed treatment opportunity.',
    talking_points: ['Scanned Amistar 250 SC on Feb 8 — follow up on purchase', 'Potato done — Kharif planning conversation', 'Largest farm in T011 at 4.64 acres'],
  },
  {
    id: 'GRW_04801', name: 'Jaswant Singh', type: 'grower' as const,
    tehsil: 'Ludhiana_T002', district: 'Ludhiana',
    lat: 30.89, lng: 75.78,
    age: 29, gender: 'male', language: 'Punjabi',
    farm_size_acres: 0.73, device: 'smartphone',
    crop: 'wheat', season: 'Rabi_2025-26',
    crop_stage: 'Tillering', crop_stage_date: '2026-01-15',
    harvest_start: '2026-03-20',
    product_scanned: false, product_name: null,
    campaign_attended: true,
    last_visit_days_ago: 6,
    priority_score: 55, priority_level: 'MEDIUM' as const,
    ai_recommendation: 'Attended campaign in Nov. Small farm but engaged — push Topik 15 WP for weed control at tillering. Convert campaign interest to sale.',
    talking_points: ['Campaign attendee — warm lead', 'Wheat at tillering — weed management now', 'Topik 15 WP appropriate for his farm size'],
  },
  {
    id: 'GRW_05685', name: 'Gurdev Singh', type: 'grower' as const,
    tehsil: 'Ludhiana_T002', district: 'Ludhiana',
    lat: 30.91, lng: 75.79,
    age: 70, gender: 'male', language: 'Punjabi',
    farm_size_acres: 0.82, device: 'smartphone',
    crop: 'potato', season: 'Rabi_2025-26',
    crop_stage: 'Harvest (done)', crop_stage_date: '2026-03-10',
    harvest_start: '2026-01-20',
    product_scanned: false, product_name: null,
    campaign_attended: true,
    last_visit_days_ago: 18,
    priority_score: 61, priority_level: 'MEDIUM' as const,
    ai_recommendation: 'Long-standing customer. Potato done. Discuss Kharif crop plans — likely vegetables. Introduce Actara 25 WG for vegetable crops.',
    talking_points: ['Campaign attended Feb 20', 'Older farmer — relationship visit important', 'Vegetable probability high next season'],
  },
  {
    id: 'GRW_05357', name: 'Sukhjinder Singh', type: 'grower' as const,
    tehsil: 'Ludhiana_T011', district: 'Ludhiana',
    lat: 30.95, lng: 75.87,
    age: 32, gender: 'male', language: 'Punjabi',
    farm_size_acres: 1.5, device: 'smartphone',
    crop: 'wheat', season: 'Rabi_2025-26',
    crop_stage: 'Flowering', crop_stage_date: '2026-02-20',
    harvest_start: '2026-03-20',
    product_scanned: false, product_name: null,
    campaign_attended: true,
    last_visit_days_ago: 4,
    priority_score: 43, priority_level: 'LOW' as const,
    ai_recommendation: 'Wheat at flowering — fungicide already applied (confirmed on visit). Check application outcome. Push Actara 25 WG for aphid watch.',
    talking_points: ['Follow-up on Tilt 250 EC applied last visit', 'Aphid pressure starting in district', 'Young progressive farmer — AI app potential'],
  },
  {
    id: 'GRW_02306', name: 'Hardeep Kaur', type: 'grower' as const,
    tehsil: 'Ludhiana_T002', district: 'Ludhiana',
    lat: 30.90, lng: 75.78,
    age: 33, gender: 'female', language: 'Punjabi',
    farm_size_acres: 2.25, device: 'smartphone',
    crop: null, season: null,
    crop_stage: 'No crop this season', crop_stage_date: null,
    harvest_start: null,
    product_scanned: false, product_name: null,
    campaign_attended: true,
    last_visit_days_ago: 45,
    priority_score: 67, priority_level: 'MEDIUM' as const,
    ai_recommendation: 'No Rabi crop this season — land likely fallow or leased. Campaign attendee Nov. Re-engage for Kharif planning. Medium farm size with potential.',
    talking_points: ['45 days since last contact — re-engagement visit', 'Campaign attended Nov 7 — initial interest noted', 'Kharif crop planning window opening — paddy/maize'],
  },
]

// Combined customers list (retailers + growers)
export const allCustomers = [...retailers, ...growers]

// Today's priority visit list (sorted by priority_score desc)
export const todayVisits = [
  ...retailers.filter(r => r.priority_level === 'HIGH'),
  ...growers.filter(g => g.priority_level === 'HIGH'),
  ...retailers.filter(r => r.priority_level === 'MEDIUM'),
  ...growers.filter(g => g.priority_level === 'MEDIUM'),
].slice(0, 8)

// AI alerts for the rep's territory
export const alerts = [
  {
    id: '1', type: 'pest' as const, severity: 'HIGH' as const, status: 'active' as const,
    title: 'Grey Leaf Spot pressure rising — Ludhiana T011',
    district: 'Ludhiana_T011, Punjab', time_ago: '2 hours ago',
    description: 'AI detected 3.2σ deviation in pest report volume from field data. 2 of your wheat growers in T011 (Paramjit Singh, Sukhjinder Singh) are at tillering/flowering — prime infection window.',
    recommended_action: 'Visit Paramjit Singh today. Recommend Tilt 250 EC application within 7 days. Also brief RTL_00130 (Ramesh Agro) to stock up — Vertimec at only 6 units.',
  },
  {
    id: '2', type: 'weather' as const, severity: 'MEDIUM' as const, status: 'active' as const,
    title: 'Rainfall deviation — fungicide timing shift',
    district: 'Ludhiana district', time_ago: '5 hours ago',
    description: 'Rainfall 38% above 30-day average this week. Wheat flowering window shifting 5 days later than crop calendar prediction.',
    recommended_action: 'Update fungicide timing advice to growers — push application by 5 days. Adjust your talking points for Jaswant Singh and Paramjit Singh visits today.',
  },
  {
    id: '3', type: 'competitor' as const, severity: 'MEDIUM' as const, status: 'active' as const,
    title: 'Competitor stock-out — opportunity window',
    district: 'Ludhiana T002, T006', time_ago: '1 day ago',
    description: 'Field reports indicate Dhanuka herbicide (Axial equivalent) out of stock at 3 agri-stores in T002 and T006. 1–2 week window to push Axial 50 EC.',
    recommended_action: 'Brief Punjab Krishi Centre (RTL_00131, T006) and Gurpreet Agro (RTL_00132, T002) to stock Axial 50 EC immediately. Offer Q2 promotional pricing.',
  },
  {
    id: '4', type: 'demand' as const, severity: 'LOW' as const, status: 'active' as const,
    title: 'Product scan signal — Amistar 250 SC interest',
    district: 'Ludhiana_T011', time_ago: '2 days ago',
    description: 'Karamjit Kaur (GRW_05117) scanned Amistar 250 SC on Feb 8 via Syngenta app — high intent signal. No purchase recorded yet.',
    recommended_action: 'Visit Karamjit Kaur soon to convert scan to purchase. She is at harvest stage — also good moment for Kharif planning conversation.',
  },
]

// My performance data (REP_0018 actual visit log derived)
export const myPerformance = {
  visits_this_week: 12,
  visits_target_week: 18,
  visits_today: 3,
  visits_target_today: 7,
  conversion_rate: 74,
  conversion_rate_delta: 3,
  mtd_revenue: 324000,
  mtd_target: 450000,
  mtd_revenue_delta: -4,
  ai_adoption: 82,
  ai_adoption_delta: 8,
  avg_order_value: 18400,
  avg_order_delta: 2,
}

// Weekly visit trend (from retailer_visit_log.csv for REP_0018 derived)
export const weeklyVisits = [
  { day: 'Mon', visits: 4, conversion: 75, type: 'Mixed' },
  { day: 'Tue', visits: 5, conversion: 80, type: 'Retailer' },
  { day: 'Wed', visits: 3, conversion: 67, type: 'Grower' },
  { day: 'Thu', visits: 4, conversion: 75, type: 'Campaign' },
  { day: 'Fri', visits: 5, conversion: 60, type: 'Mixed' },
  { day: 'Sat', visits: 3, conversion: 100, type: 'Retailer' },
]

// Products sold (from retailer_pos.csv for Ludhiana retailers derived)
export const productRevenue = [
  { product: 'Tilt 250 EC', revenue: 284000, units: 312 },
  { product: 'Amistar 250 SC', revenue: 198000, units: 187 },
  { product: 'Axial 50 EC', revenue: 156000, units: 201 },
  { product: 'Vertimec 1.8 EC', revenue: 134000, units: 98 },
  { product: 'Actara 25 WG', revenue: 112000, units: 143 },
  { product: 'Topik 15 WP', revenue: 89000, units: 167 },
]

// Visit log (from retailer_visit_log.csv for REP_0018)
export const visitLog = [
  { date: '2026-03-29', tehsil: 'Ludhiana_T002', type: 'retailer meeting', product: 'Amistar 250 SC', customer: 'Gurpreet Agro Traders' },
  { date: '2026-03-28', tehsil: 'Ludhiana_T007', type: 'grower meeting', product: 'Axial 50 EC', customer: 'Harpreet Grower' },
  { date: '2026-03-26', tehsil: 'Ludhiana_T003', type: 'retailer meeting', product: 'Kavach 75 WP', customer: 'T003 Retailer' },
  { date: '2026-03-25', tehsil: 'Ludhiana_T008', type: 'retailer meeting', product: 'Axial 50 EC', customer: 'T008 Retailer' },
  { date: '2026-03-24', tehsil: 'Ludhiana_T006', type: 'grower meeting', product: 'Amistar 250 SC', customer: 'T006 Grower' },
  { date: '2026-03-23', tehsil: 'Ludhiana_T001', type: 'campaign_conducted', product: 'Amistar 250 SC', customer: 'T001 Campaign' },
]

// Demand forecast (what to push in territory)
export const forecastData = [
  { date: 'Apr 1', predicted: 420, baseline: 310, low: 380, high: 460 },
  { date: 'Apr 2', predicted: 510, baseline: 320, low: 470, high: 550 },
  { date: 'Apr 3', predicted: 680, baseline: 315, low: 620, high: 740 },
  { date: 'Apr 4', predicted: 590, baseline: 308, low: 540, high: 640 },
  { date: 'Apr 5', predicted: 450, baseline: 312, low: 410, high: 490 },
  { date: 'Apr 6', predicted: 380, baseline: 305, low: 340, high: 420 },
  { date: 'Apr 7', predicted: 340, baseline: 310, low: 300, high: 380 },
]

export const districtForecast = [
  { tehsil: 'Ludhiana_T001', stock: 340, demand: 520, gap: -180, urgency: 'HIGH' as const },
  { tehsil: 'Ludhiana_T006', stock: 210, demand: 290, gap: -80, urgency: 'MEDIUM' as const },
  { tehsil: 'Ludhiana_T009', stock: 480, demand: 310, gap: 170, urgency: 'OK' as const },
  { tehsil: 'Ludhiana_T011', stock: 190, demand: 220, gap: -30, urgency: 'MEDIUM' as const },
  { tehsil: 'Ludhiana_T002', stock: 560, demand: 410, gap: 150, urgency: 'OK' as const },
]

// WhatsApp campaign engagement (from whatsapp_campaign.csv for Ludhiana growers)
export const campaignStats = {
  sent: 23, delivered: 21, opened: 8, clicked: 3,
  product: 'Tilt 250 EC', crop: 'wheat',
}
