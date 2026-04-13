import { cn } from '@/lib/utils'
import { AlertTriangle } from 'lucide-react'

interface SoilMapUnit {
  mukey: string
  musym: string
  muname: string
  muacres: number
  hydric: boolean
  drainage_class: string | null
  hydric_rating: string | null
  farmland_class: string | null
  tax_class: string | null
  dominant_component: string | null
  dominant_pct: number | null
  corr_steel: string | null
  corr_concrete: string | null
  uscs_class: string | null
  color: string
}

interface SoilsSummaryData {
  map_unit_count: number
  hydric_present: boolean
  hydric_count: number
  map_units: SoilMapUnit[]
  summary: {
    drainage_classes: Record<string, number>
    hydric_unit_names: string[]
  }
}

interface SoilsSummaryCardProps {
  data: SoilsSummaryData
}

function CorrosivityBadge({ rating }: { rating: string | null }) {
  if (!rating) return <span className="text-gray-400">—</span>
  const level = rating.toLowerCase()
  return (
    <span className={cn(
      'px-1.5 py-0.5 rounded text-xs font-medium',
      level === 'low'      && 'bg-green-50 text-green-700',
      level === 'moderate' && 'bg-amber-50 text-amber-700',
      level === 'high'     && 'bg-red-50 text-red-700',
      !['low','moderate','high'].includes(level) && 'bg-gray-100 text-gray-600',
    )}>
      {rating}
    </span>
  )
}

function DrainageDot({ drainageClass }: { drainageClass: string | null }) {
  const cls = drainageClass || ''
  const color =
    cls.includes('Very poorly') ? '#1e3a8a' :
    cls.includes('Poorly')      ? '#1d4ed8' :
    cls.includes('Somewhat poorly') ? '#3b82f6' :
    cls.includes('Moderately') ? '#86efac' :
    cls.includes('Well drained') ? '#16a34a' :
    cls.includes('excessively') ? '#f59e0b' :
    '#a3a3a3'

  return (
    <span
      className="inline-block w-2 h-2 rounded-full flex-shrink-0"
      style={{ backgroundColor: color }}
    />
  )
}

export function SoilsSummaryCard({ data }: SoilsSummaryCardProps) {
  const hydricUnits = data.map_units.filter((mu) => mu.hydric)
  const otherUnits  = data.map_units.filter((mu) => !mu.hydric)

  return (
    <div className="space-y-3 text-xs">
      {/* Hydric flag banner */}
      {data.hydric_present && (
        <div className="flex items-start gap-2 bg-blue-50 border border-blue-200 rounded p-2">
          <AlertTriangle className="w-3.5 h-3.5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-blue-800">Hydric soils present</span>
            <p className="text-blue-700 mt-0.5 leading-snug">
              {data.hydric_count} unit{data.hydric_count !== 1 ? 's' : ''} indicate
              wetland hydrology — CWA §404 review recommended.
            </p>
          </div>
        </div>
      )}

      {/* Map unit list */}
      <div className="space-y-1.5">
        {/* Hydric units first */}
        {hydricUnits.map((mu) => (
          <MapUnitRow key={mu.mukey} mu={mu} />
        ))}
        {otherUnits.map((mu) => (
          <MapUnitRow key={mu.mukey} mu={mu} />
        ))}
      </div>

      {/* Footer */}
      <div className="text-gray-400 text-right">
        {data.map_unit_count} map unit{data.map_unit_count !== 1 ? 's' : ''} · USDA SSURGO
      </div>
    </div>
  )
}

function MapUnitRow({ mu }: { mu: SoilMapUnit }) {
  return (
    <div className={cn(
      'rounded border p-2 space-y-1.5',
      mu.hydric ? 'bg-blue-50 border-blue-200' : 'bg-white',
    )}>
      {/* Header row */}
      <div className="flex items-center gap-1.5">
        <span
          className="w-2.5 h-2.5 rounded-sm flex-shrink-0"
          style={{ backgroundColor: mu.color }}
        />
        <span className="font-semibold text-slate truncate flex-1">{mu.musym}</span>
        {mu.hydric && (
          <span className="bg-blue-600 text-white text-[10px] px-1.5 py-0.5 rounded font-bold flex-shrink-0">
            HYDRIC
          </span>
        )}
      </div>

      {/* Map unit name */}
      <div className="text-gray-600 leading-snug">{mu.muname}</div>

      {/* Attributes grid */}
      <div className="grid grid-cols-2 gap-x-2 gap-y-0.5">
        {mu.drainage_class && (
          <>
            <span className="text-gray-400 flex items-center gap-1">
              <DrainageDot drainageClass={mu.drainage_class} />
              Drainage
            </span>
            <span className="text-gray-700 truncate">{mu.drainage_class}</span>
          </>
        )}
        {mu.farmland_class && (
          <>
            <span className="text-gray-400">Farmland</span>
            <span className={cn(
              'truncate',
              mu.farmland_class === 'Prime farmland' ? 'text-green-700 font-medium' : 'text-gray-700',
            )}>
              {mu.farmland_class}
            </span>
          </>
        )}
        {mu.uscs_class && (
          <>
            <span className="text-gray-400">USCS</span>
            <span className="text-gray-700 font-mono">{mu.uscs_class}</span>
          </>
        )}
      </div>

      {/* Engineering interpretations */}
      {(mu.corr_steel || mu.corr_concrete) && (
        <div className="border-t pt-1 mt-1 grid grid-cols-2 gap-x-2 items-center">
          <span className="text-gray-400">Corr. Steel</span>
          <CorrosivityBadge rating={mu.corr_steel} />
          <span className="text-gray-400">Corr. Concrete</span>
          <CorrosivityBadge rating={mu.corr_concrete} />
        </div>
      )}

      {/* Taxonomy */}
      {mu.tax_class && (
        <div className="text-gray-400 leading-snug truncate" title={mu.tax_class}>
          {mu.tax_class}
        </div>
      )}
    </div>
  )
}
