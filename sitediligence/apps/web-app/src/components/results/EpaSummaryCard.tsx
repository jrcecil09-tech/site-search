import { AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface FrsFacility {
  registry_id: string
  name: string
  city: string
  state: string
  programs: string[]
  lat: number | null
  lon: number | null
  category: string
  color: string
}

interface EchoFacility {
  registry_id: string
  name: string
  compliance_status: { air: string; water: string; waste: string }
  total_violations: number
  formal_actions: number
  has_violation: boolean
  facility_type: string
  category: string
}

interface SuperfundSite {
  site_id: string
  name: string
  city: string
  state: string
  status: string
  npl_status: string
  distance_miles: number | null
  category: string
}

interface RcraHandler {
  handler_id: string
  name: string
  city: string
  active: boolean
  category: string
}

interface TriFacility {
  facility_id: string
  name: string
  city: string
  sic_code: string
  category: string
}

interface EpaSummaryData {
  flag: boolean
  frs_facilities: FrsFacility[]
  echo_facilities: EchoFacility[]
  superfund_sites: SuperfundSite[]
  rcra_handlers: RcraHandler[]
  tri_facilities: TriFacility[]
  summary: {
    frs_count: number
    echo_count: number
    echo_violations: number
    formal_actions: number
    superfund_count: number
    superfund_near_count: number
    rcra_count: number
    tri_count: number
    superfund_flag: boolean
    near_superfund_names: string[]
  }
  display: {
    color_superfund: string
    color_rcra: string
    color_tri: string
    color_frs: string
    buffer_miles: number
  }
}

interface EpaSummaryCardProps {
  data: EpaSummaryData
}

function CategoryDot({ color }: { color: string }) {
  return (
    <span
      className="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0"
      style={{ backgroundColor: color }}
    />
  )
}

function ComplianceChip({ status }: { status: string }) {
  const isViolation = status.toLowerCase().includes('violation')
  return (
    <span className={cn(
      'text-[10px] px-1 py-0.5 rounded',
      isViolation ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700',
    )}>
      {status || 'Unknown'}
    </span>
  )
}

export function EpaSummaryCard({ data }: EpaSummaryCardProps) {
  const { summary, display } = data

  return (
    <div className="space-y-3 text-xs">
      {/* Superfund flag banner */}
      {data.flag && (
        <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded p-2">
          <AlertTriangle className="w-3.5 h-3.5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-red-800">
              Superfund site within {0.5} miles
            </span>
            {summary.near_superfund_names.map((n) => (
              <p key={n} className="text-red-700 mt-0.5 leading-snug">{n}</p>
            ))}
          </div>
        </div>
      )}

      {/* Risk count grid */}
      <div className="grid grid-cols-2 gap-1.5">
        <CountTile
          color={display.color_superfund}
          label="Superfund"
          count={summary.superfund_count}
          sub={summary.superfund_near_count > 0
            ? `${summary.superfund_near_count} within 0.5 mi`
            : undefined}
          alert={summary.superfund_near_count > 0}
        />
        <CountTile
          color={display.color_rcra}
          label="RCRA Hazardous"
          count={summary.rcra_count}
        />
        <CountTile
          color={display.color_tri}
          label="TRI Toxic Release"
          count={summary.tri_count}
        />
        <CountTile
          color={display.color_frs}
          label="EPA Violations"
          count={summary.echo_violations}
          sub={summary.formal_actions > 0
            ? `${summary.formal_actions} formal action${summary.formal_actions !== 1 ? 's' : ''}`
            : undefined}
          alert={summary.echo_violations > 0}
        />
      </div>

      {/* Superfund sites */}
      {data.superfund_sites.length > 0 && (
        <section>
          <SectionHeader color={display.color_superfund} label="Superfund / CERCLA Sites" />
          {data.superfund_sites.map((s) => (
            <div key={s.site_id} className="flex items-start gap-2 py-1 border-b border-gray-100 last:border-0">
              <CategoryDot color={display.color_superfund} />
              <div className="flex-1 min-w-0">
                <div className="font-medium text-slate truncate">{s.name}</div>
                <div className="text-gray-400">{s.city}, {s.state}</div>
                {s.npl_status && (
                  <div className="text-red-600 text-[10px]">{s.npl_status}</div>
                )}
              </div>
              {s.distance_miles !== null && (
                <span className={cn(
                  'flex-shrink-0 font-mono text-[10px] px-1.5 py-0.5 rounded',
                  s.distance_miles <= 0.5
                    ? 'bg-red-100 text-red-700 font-bold'
                    : 'bg-gray-100 text-gray-600',
                )}>
                  {s.distance_miles.toFixed(2)} mi
                </span>
              )}
            </div>
          ))}
        </section>
      )}

      {/* RCRA hazardous waste */}
      {data.rcra_handlers.length > 0 && (
        <section>
          <SectionHeader color={display.color_rcra} label="RCRA Hazardous Waste" />
          {data.rcra_handlers.map((r) => (
            <div key={r.handler_id} className="flex items-center gap-2 py-0.5 border-b border-gray-100 last:border-0">
              <CategoryDot color={display.color_rcra} />
              <span className="flex-1 truncate text-gray-700">{r.name}</span>
              {r.active && (
                <span className="text-[10px] bg-orange-50 text-orange-700 px-1 py-0.5 rounded flex-shrink-0">
                  Active
                </span>
              )}
            </div>
          ))}
        </section>
      )}

      {/* TRI toxic release */}
      {data.tri_facilities.length > 0 && (
        <section>
          <SectionHeader color={display.color_tri} label="TRI Toxic Release Inventory" />
          {data.tri_facilities.map((t) => (
            <div key={t.facility_id} className="flex items-center gap-2 py-0.5 border-b border-gray-100 last:border-0">
              <CategoryDot color={display.color_tri} />
              <span className="flex-1 truncate text-gray-700">{t.name}</span>
              {t.sic_code && (
                <span className="text-gray-400 text-[10px] font-mono flex-shrink-0">
                  SIC {t.sic_code}
                </span>
              )}
            </div>
          ))}
        </section>
      )}

      {/* ECHO enforcement */}
      {data.echo_facilities.filter((f) => f.has_violation).length > 0 && (
        <section>
          <SectionHeader color={display.color_frs} label="ECHO Compliance Violations" />
          {data.echo_facilities.filter((f) => f.has_violation).map((f) => (
            <div key={f.registry_id} className="py-1 border-b border-gray-100 last:border-0">
              <div className="flex items-center gap-2">
                <CategoryDot color={display.color_frs} />
                <span className="flex-1 font-medium truncate text-slate">{f.name}</span>
                <span className="text-red-600 font-mono text-[10px] flex-shrink-0">
                  {f.total_violations}v / {f.formal_actions}fa
                </span>
              </div>
              <div className="flex gap-1 mt-1 ml-4 flex-wrap">
                {f.compliance_status.air   && <ComplianceChip status={f.compliance_status.air} />}
                {f.compliance_status.water && <ComplianceChip status={f.compliance_status.water} />}
                {f.compliance_status.waste && <ComplianceChip status={f.compliance_status.waste} />}
              </div>
            </div>
          ))}
        </section>
      )}

      {/* FRS regulated facilities */}
      {data.frs_facilities.length > 0 && (
        <section>
          <SectionHeader color={display.color_frs} label="Regulated Facilities (FRS)" />
          {data.frs_facilities.slice(0, 5).map((f) => (
            <div key={f.registry_id} className="flex items-center gap-2 py-0.5 border-b border-gray-100 last:border-0">
              <CategoryDot color={display.color_frs} />
              <span className="flex-1 truncate text-gray-700">{f.name}</span>
              {f.programs.length > 0 && (
                <span className="text-gray-400 text-[10px] flex-shrink-0">
                  {f.programs.slice(0, 3).join(' · ')}
                </span>
              )}
            </div>
          ))}
        </section>
      )}

      <div className="text-gray-400 text-right">
        Within {data.display.buffer_miles} mile · EPA FRS / ECHO / Envirofacts
      </div>
    </div>
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
      alert && count > 0 ? 'bg-red-50 border-red-200' : 'bg-white',
    )}>
      <div className="flex items-center gap-1.5 mb-0.5">
        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
        <span className="text-gray-500 truncate">{label}</span>
      </div>
      <div className={cn(
        'text-lg font-bold',
        alert && count > 0 ? 'text-red-700' : 'text-slate',
      )}>
        {count}
      </div>
      {sub && <div className="text-[10px] text-gray-400 leading-snug">{sub}</div>}
    </div>
  )
}
