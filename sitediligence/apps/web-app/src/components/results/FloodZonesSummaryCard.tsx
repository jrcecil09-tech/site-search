import { cn } from '@/lib/utils'

interface FloodZoneData {
  zone_count: number
  flood_zones: Array<{
    fld_zone: string
    zone_subtype: string | null
    static_bfe: number | null
    sfha: boolean
    is_floodway: boolean
    firm_panel: string | null
    color: string
  }>
  summary: {
    zones_found: string[]
    sfha_present: boolean
    zone_ae_present: boolean
    firm_panels: string[]
    bfe_range_ft: { min: number; max: number } | null
  }
}

interface FloodZonesSummaryCardProps {
  data: FloodZoneData
}

export function FloodZonesSummaryCard({ data }: FloodZonesSummaryCardProps) {
  const { summary } = data

  const bfeText = summary.bfe_range_ft
    ? summary.bfe_range_ft.min === summary.bfe_range_ft.max
      ? `${summary.bfe_range_ft.min} ft`
      : `${summary.bfe_range_ft.min}–${summary.bfe_range_ft.max} ft`
    : null

  return (
    <div className="space-y-3 text-xs">
      <div className="flex flex-wrap gap-1.5">
        {summary.sfha_present && (
          <span className="font-bold px-2 py-0.5 rounded bg-orange-100 text-orange-700">
            ⚑ SFHA Present
          </span>
        )}
        {summary.zone_ae_present && (
          <span className="font-bold px-2 py-0.5 rounded bg-red-100 text-red-700">
            Zone AE
          </span>
        )}
        {!summary.sfha_present && (
          <span className="font-bold px-2 py-0.5 rounded bg-green-100 text-green-700">
            No SFHA
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div className="bg-white rounded p-2 border">
          <div className="text-gray-500">Zones Found</div>
          <div className="text-sm font-semibold mt-0.5">
            {summary.zones_found.join(', ')}
          </div>
          <div className="text-gray-400">{data.zone_count} polygons</div>
        </div>
        {bfeText && (
          <div className="bg-white rounded p-2 border">
            <div className="text-gray-500">Base Flood Elev.</div>
            <div className="text-sm font-semibold mt-0.5">{bfeText}</div>
            <div className="text-gray-400">NAVD 88</div>
          </div>
        )}
      </div>

      <div>
        <div className="text-gray-500 font-medium mb-1">Zone Breakdown</div>
        {data.flood_zones.map((z, i) => (
          <div key={i} className="flex items-center gap-2 py-0.5 border-b border-gray-100 last:border-0">
            <div
              className="w-2.5 h-2.5 rounded-sm flex-shrink-0 border border-gray-200"
              style={{ backgroundColor: z.color }}
            />
            <span className={cn('font-medium', z.sfha ? 'text-orange-700' : 'text-gray-600')}>
              {z.fld_zone}
              {z.is_floodway && ' (Floodway)'}
            </span>
            {z.zone_subtype && (
              <span className="text-gray-400 truncate">{z.zone_subtype}</span>
            )}
            {z.static_bfe !== null && (
              <span className="ml-auto text-gray-500 flex-shrink-0">{z.static_bfe} ft BFE</span>
            )}
          </div>
        ))}
      </div>

      {summary.firm_panels.length > 0 && (
        <div>
          <div className="text-gray-500 font-medium mb-1">FIRM Panels</div>
          {summary.firm_panels.map((panel) => (
            <div key={panel} className="font-mono text-gray-600 py-0.5">
              {panel}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
