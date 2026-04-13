import { useState } from 'react'
import { AlertTriangle, ChevronDown, ChevronRight, ExternalLink } from 'lucide-react'
import { cn } from '@/lib/utils'

// ── Types ─────────────────────────────────────────────────────────────────────

interface NrhpProperty {
  refnum: string
  name: string
  city: string
  state: string
  county: string
  category: string      // Building | District | Object | Site | Structure
  date_listed: string | null
  lat: number | null
  lon: number | null
  distance_miles: number | null
  near_flag: boolean
  category_code: string
  color: string
}

interface CemeteryFeature {
  gnis_id: string
  name: string
  state: string
  county: string
  lat: number | null
  lon: number | null
  distance_miles: number | null
  near_flag: boolean
  category_code: string
  color: string
}

interface ShpoEntry {
  abbr: string
  name: string
  url: string
}

interface HistoricSummaryData {
  flag: boolean
  nrhp_properties: NrhpProperty[]
  cemeteries: CemeteryFeature[]
  shpo_data: ShpoEntry[]
  summary: {
    nrhp_count: number
    nrhp_near_count: number
    cemetery_count: number
    cemetery_near_count: number
    section_106_required: boolean
    near_nrhp_names: string[]
    near_cemetery_names: string[]
  }
  display: {
    color_nrhp: string
    color_cemetery: string
    buffer_miles: number
    flag_distance_ft: number
  }
}

interface HistoricSummaryCardProps {
  data: HistoricSummaryData
}

// ── Sub-components ────────────────────────────────────────────────────────────

function CategoryDot({ color }: { color: string }) {
  return (
    <span
      className="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0"
      style={{ backgroundColor: color }}
    />
  )
}

function SectionHeader({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1.5 mb-1">
      <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
      <span className="font-medium text-gray-500">{label}</span>
    </div>
  )
}

function CountTile({
  color, label, count, sub, alert,
}: {
  color: string
  label: string
  count: number
  sub?: string
  alert?: boolean
}) {
  return (
    <div className={cn(
      'rounded border p-2',
      alert && count > 0 ? 'bg-amber-50 border-amber-200' : 'bg-white',
    )}>
      <div className="flex items-center gap-1.5 mb-0.5">
        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
        <span className="text-gray-500 truncate">{label}</span>
      </div>
      <div className={cn(
        'text-lg font-bold',
        alert && count > 0 ? 'text-amber-700' : 'text-slate',
      )}>
        {count}
      </div>
      {sub && <div className="text-[10px] text-gray-400 leading-snug">{sub}</div>}
    </div>
  )
}

function CategoryBadge({ category }: { category: string }) {
  const colours: Record<string, string> = {
    Building:   'bg-blue-50 text-blue-700',
    District:   'bg-purple-50 text-purple-700',
    Site:       'bg-green-50 text-green-700',
    Structure:  'bg-orange-50 text-orange-700',
    Object:     'bg-gray-50 text-gray-600',
  }
  return (
    <span className={cn(
      'text-[10px] px-1 py-0.5 rounded flex-shrink-0 font-medium',
      colours[category] ?? 'bg-gray-50 text-gray-600',
    )}>
      {category || 'Unknown'}
    </span>
  )
}

function DistanceBadge({
  distMiles,
  flagFt,
}: {
  distMiles: number | null
  flagFt: number
}) {
  if (distMiles === null) return null
  const flagMiles = flagFt / 5_280
  const isNear = distMiles <= flagMiles
  const ftLabel = distMiles < 0.2
    ? `${Math.round(distMiles * 5_280)} ft`
    : `${distMiles.toFixed(2)} mi`
  return (
    <span className={cn(
      'flex-shrink-0 font-mono text-[10px] px-1.5 py-0.5 rounded',
      isNear
        ? 'bg-amber-100 text-amber-800 font-bold'
        : 'bg-gray-100 text-gray-600',
    )}>
      {ftLabel}
    </span>
  )
}

// ── SHPO table (collapsible) ──────────────────────────────────────────────────

function ShpoCard({ data }: { data: ShpoEntry[] }) {
  const [open, setOpen] = useState(false)

  return (
    <div className="border rounded overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
      >
        <div>
          <div className="font-medium text-gray-700 text-xs">State SHPO Contacts</div>
          <div className="text-[10px] text-gray-400 mt-0.5">
            {data.length} state offices · click to expand
          </div>
        </div>
        {open
          ? <ChevronDown className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
          : <ChevronRight className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />}
      </button>

      {open && (
        <div className="p-2 bg-white">
          {/* Consulting instructions */}
          <div className="mb-2 p-2 bg-blue-50 border border-blue-100 rounded text-[11px] text-blue-800 leading-snug">
            <strong>Section 106 / State SHPO consultation</strong> may be required when
            a project involves federal permits, licenses, or funding and could affect
            historic properties. Contact the SHPO for the project state early in the
            planning process.
            <br />
            <span className="text-blue-600 mt-0.5 block">
              To add a state-specific GIS layer endpoint, update{' '}
              <code className="bg-blue-100 px-0.5 rounded">services/queries/historic.py</code>{' '}
              with the state ArcGIS REST URL for the state&apos;s SHPO survey layer.
            </span>
          </div>

          {/* SHPO table */}
          <div className="max-h-64 overflow-y-auto">
            <table className="w-full text-[11px]">
              <thead className="sticky top-0 bg-gray-50">
                <tr>
                  <th className="text-left py-1 px-1 text-gray-500 font-medium w-8">ST</th>
                  <th className="text-left py-1 px-1 text-gray-500 font-medium">State</th>
                  <th className="text-left py-1 px-1 text-gray-500 font-medium">SHPO Website</th>
                </tr>
              </thead>
              <tbody>
                {data.map((s) => (
                  <tr key={s.abbr} className="border-t border-gray-100 hover:bg-gray-50">
                    <td className="py-0.5 px-1 font-mono text-gray-500">{s.abbr}</td>
                    <td className="py-0.5 px-1 text-gray-700">{s.name}</td>
                    <td className="py-0.5 px-1">
                      <a
                        href={s.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline flex items-center gap-0.5 truncate max-w-[140px]"
                      >
                        <span className="truncate">{s.url.replace(/^https?:\/\//, '')}</span>
                        <ExternalLink className="w-2.5 h-2.5 flex-shrink-0" />
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Main card ─────────────────────────────────────────────────────────────────

export function HistoricSummaryCard({ data }: HistoricSummaryCardProps) {
  const { summary, display } = data
  const flagFt = display.flag_distance_ft ?? 500

  return (
    <div className="space-y-3 text-xs">

      {/* Flag banners */}
      {data.flag && (
        <div className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded p-2">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            {summary.section_106_required && (
              <p className="font-semibold text-amber-800">
                NRHP property within {flagFt} ft — Section 106 consultation required
              </p>
            )}
            {summary.cemetery_near_count > 0 && (
              <p className="font-semibold text-amber-800">
                Cemetery within {flagFt} ft — avoid disturbance, cultural sensitivity required
              </p>
            )}
            {summary.near_nrhp_names.map((n) => (
              <p key={n} className="text-amber-700 leading-snug">· {n}</p>
            ))}
            {summary.near_cemetery_names.map((n) => (
              <p key={n} className="text-amber-700 leading-snug">· {n}</p>
            ))}
          </div>
        </div>
      )}

      {/* Count tiles */}
      <div className="grid grid-cols-2 gap-1.5">
        <CountTile
          color={display.color_nrhp}
          label="NRHP Listed"
          count={summary.nrhp_count}
          sub={summary.nrhp_near_count > 0
            ? `${summary.nrhp_near_count} within ${flagFt} ft`
            : `within ${display.buffer_miles} mi`}
          alert={summary.nrhp_near_count > 0}
        />
        <CountTile
          color={display.color_cemetery}
          label="Cemeteries"
          count={summary.cemetery_count}
          sub={summary.cemetery_near_count > 0
            ? `${summary.cemetery_near_count} within ${flagFt} ft`
            : undefined}
          alert={summary.cemetery_near_count > 0}
        />
      </div>

      {/* NRHP listed properties */}
      {data.nrhp_properties.length > 0 && (
        <section>
          <SectionHeader color={display.color_nrhp} label="NRHP Listed Properties" />
          {data.nrhp_properties.map((p) => (
            <div
              key={p.refnum || p.name}
              className="flex items-start gap-2 py-1 border-b border-gray-100 last:border-0"
            >
              <CategoryDot color={display.color_nrhp} />
              <div className="flex-1 min-w-0">
                <div className="font-medium text-slate truncate">{p.name}</div>
                <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
                  {p.category && <CategoryBadge category={p.category} />}
                  {p.date_listed && (
                    <span className="text-gray-400">Listed {p.date_listed.slice(0, 4)}</span>
                  )}
                </div>
                {(p.city || p.state) && (
                  <div className="text-gray-400 mt-0.5">
                    {[p.city, p.state].filter(Boolean).join(', ')}
                    {p.refnum && (
                      <span className="ml-1.5 font-mono text-[10px]">#{p.refnum}</span>
                    )}
                  </div>
                )}
              </div>
              <DistanceBadge distMiles={p.distance_miles} flagFt={flagFt} />
            </div>
          ))}
        </section>
      )}

      {/* Cemeteries */}
      {data.cemeteries.length > 0 && (
        <section>
          <SectionHeader color={display.color_cemetery} label="Cemetery Features (USGS GNIS)" />
          {data.cemeteries.map((c) => (
            <div
              key={c.gnis_id || c.name}
              className="flex items-start gap-2 py-1 border-b border-gray-100 last:border-0"
            >
              <CategoryDot color={display.color_cemetery} />
              <div className="flex-1 min-w-0">
                <div className="font-medium text-slate truncate">{c.name}</div>
                <div className="flex items-center gap-2 mt-0.5 text-gray-400">
                  {c.gnis_id && (
                    <span className="font-mono text-[10px]">GNIS {c.gnis_id}</span>
                  )}
                  {(c.county || c.state) && (
                    <span>{[c.county, c.state].filter(Boolean).join(', ')}</span>
                  )}
                </div>
                {c.lat !== null && c.lon !== null && (
                  <div className="font-mono text-[10px] text-gray-300 mt-0.5">
                    {c.lat?.toFixed(5)}, {c.lon?.toFixed(5)}
                  </div>
                )}
              </div>
              <DistanceBadge distMiles={c.distance_miles} flagFt={flagFt} />
            </div>
          ))}
        </section>
      )}

      {/* State SHPO placeholder card */}
      {data.shpo_data && data.shpo_data.length > 0 && (
        <ShpoCard data={data.shpo_data} />
      )}

      <div className="text-gray-400 text-right">
        Within {display.buffer_miles} mi · NPS NRHP / USGS GNIS
      </div>
    </div>
  )
}
