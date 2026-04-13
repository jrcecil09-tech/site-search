import { cn } from '@/lib/utils'
import { Download } from 'lucide-react'

interface ContourSet {
  interval_ft: number
  color: string
  level_count: number
}

interface DemDownload {
  title: string
  download_url: string
  size_mb: number
}

interface ElevationStats {
  min_ft: number | null
  max_ft: number | null
  mean_ft: number | null
  min_m: number | null
  max_m: number | null
  mean_m: number | null
  relief_ft: number | null
  slope_min_deg: number | null
  slope_max_deg: number | null
  slope_mean_deg: number | null
}

interface ElevationData {
  centroid_elevation_ft: number | null
  centroid_elevation_m: number | null
  sample_count: number
  stats: ElevationStats
  contours: ContourSet[]
  dem_downloads: DemDownload[]
}

interface ElevationSummaryCardProps {
  data: ElevationData
}

function fmt1(v: number | null): string {
  return v !== null && v !== undefined ? v.toFixed(1) : '—'
}

function slopeLabel(deg: number | null): string {
  if (deg === null) return '—'
  if (deg < 2)  return 'Nearly flat'
  if (deg < 5)  return 'Gentle'
  if (deg < 10) return 'Moderate'
  if (deg < 20) return 'Steep'
  return 'Very steep'
}

export function ElevationSummaryCard({ data }: ElevationSummaryCardProps) {
  const { stats } = data

  return (
    <div className="space-y-3 text-xs">
      {/* Centroid elevation hero */}
      <div className="bg-white rounded p-2.5 border text-center">
        <div className="text-gray-500 mb-0.5">Site Elevation</div>
        <div className="text-xl font-bold text-slate">
          {fmt1(data.centroid_elevation_ft)} ft
        </div>
        <div className="text-gray-400">{fmt1(data.centroid_elevation_m)} m</div>
      </div>

      {/* Min / Max / Relief grid */}
      <div className="grid grid-cols-3 gap-1.5">
        <div className="bg-white rounded p-2 border text-center">
          <div className="text-gray-400">Min</div>
          <div className="font-semibold">{fmt1(stats.min_ft)} ft</div>
          <div className="text-gray-400">{fmt1(stats.min_m)} m</div>
        </div>
        <div className="bg-white rounded p-2 border text-center">
          <div className="text-gray-400">Max</div>
          <div className="font-semibold">{fmt1(stats.max_ft)} ft</div>
          <div className="text-gray-400">{fmt1(stats.max_m)} m</div>
        </div>
        <div className="bg-white rounded p-2 border text-center">
          <div className="text-gray-400">Relief</div>
          <div className="font-semibold">{fmt1(stats.relief_ft)} ft</div>
        </div>
      </div>

      {/* Slope */}
      <div className="bg-white rounded p-2 border">
        <div className="flex justify-between items-baseline">
          <span className="text-gray-500 font-medium">Slope</span>
          <span className={cn(
            'font-bold px-1.5 py-0.5 rounded',
            (stats.slope_max_deg ?? 0) > 10
              ? 'bg-amber-100 text-amber-700'
              : 'bg-green-50 text-green-700',
          )}>
            {slopeLabel(stats.slope_mean_deg)}
          </span>
        </div>
        <div className="grid grid-cols-3 mt-1.5 gap-1 text-center">
          <div>
            <div className="text-gray-400">Min</div>
            <div className="font-medium">{fmt1(stats.slope_min_deg)}°</div>
          </div>
          <div>
            <div className="text-gray-400">Mean</div>
            <div className="font-medium">{fmt1(stats.slope_mean_deg)}°</div>
          </div>
          <div>
            <div className="text-gray-400">Max</div>
            <div className="font-medium">{fmt1(stats.slope_max_deg)}°</div>
          </div>
        </div>
      </div>

      {/* Contour intervals */}
      {data.contours.length > 0 && (
        <div>
          <div className="text-gray-500 font-medium mb-1">Contour Intervals</div>
          {data.contours.map((c) => (
            <div key={c.interval_ft} className="flex items-center gap-2 py-0.5">
              <div
                className="w-6 h-0.5 flex-shrink-0 rounded"
                style={{ backgroundColor: c.color }}
              />
              <span className="text-gray-600">{c.interval_ft} ft interval</span>
              <span className="ml-auto text-gray-400">{c.level_count} lines</span>
            </div>
          ))}
        </div>
      )}

      {/* DEM download links */}
      {data.dem_downloads.length > 0 && (
        <div>
          <div className="text-gray-500 font-medium mb-1">DEM Download (1/3″)</div>
          {data.dem_downloads.map((dl, i) => (
            <a
              key={i}
              href={dl.download_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-blue-600 hover:text-blue-800 hover:underline py-0.5 truncate"
            >
              <Download className="w-3 h-3 flex-shrink-0" />
              <span className="truncate">{dl.title}</span>
              {dl.size_mb > 0 && (
                <span className="text-gray-400 flex-shrink-0 ml-auto">{dl.size_mb} MB</span>
              )}
            </a>
          ))}
        </div>
      )}

      <div className="text-gray-400 text-right">
        {data.sample_count} grid samples · USGS 3DEP 1/3″
      </div>
    </div>
  )
}
