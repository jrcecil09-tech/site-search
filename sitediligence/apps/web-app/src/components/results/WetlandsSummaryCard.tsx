import { cn } from '@/lib/utils'

interface WetlandsData {
  wetland_count: number
  total_wetland_acres: number
  regulated_404_acres: number
  summary: {
    regulated_404: boolean
    by_system: Record<string, number>
  }
  wetlands: Array<{
    wetland_type: string
    system: string
    acres: number
    regulated_404: boolean
    color: string
  }>
}

interface WetlandsSummaryCardProps {
  data: WetlandsData
}

export function WetlandsSummaryCard({ data }: WetlandsSummaryCardProps) {
  const { summary } = data

  return (
    <div className="space-y-3 text-xs">
      <span
        className={cn(
          'inline-block font-bold px-2 py-0.5 rounded',
          summary.regulated_404
            ? 'bg-red-100 text-red-700'
            : 'bg-green-100 text-green-700',
        )}
      >
        {summary.regulated_404 ? '⚑ CWA §404 Regulated' : 'No §404 Wetlands'}
      </span>

      <div className="grid grid-cols-2 gap-2">
        <div className="bg-white rounded p-2 border">
          <div className="text-gray-500">Total Wetlands</div>
          <div className="text-sm font-semibold mt-0.5">
            {data.total_wetland_acres.toFixed(1)} ac
          </div>
          <div className="text-gray-400">{data.wetland_count} features</div>
        </div>
        <div className="bg-white rounded p-2 border">
          <div className="text-gray-500">§404 Regulated</div>
          <div className="text-sm font-semibold text-red-600 mt-0.5">
            {data.regulated_404_acres.toFixed(1)} ac
          </div>
        </div>
      </div>

      <div>
        <div className="text-gray-500 font-medium mb-1">By System</div>
        {Object.entries(summary.by_system).map(([system, count]) => (
          <div key={system} className="flex justify-between py-0.5 border-b border-gray-100 last:border-0">
            <span className="text-gray-600">{system}</span>
            <span className="font-medium">{count} features</span>
          </div>
        ))}
      </div>

      <div>
        <div className="text-gray-500 font-medium mb-1">Wetland Types</div>
        {data.wetlands.slice(0, 5).map((w, i) => (
          <div key={i} className="flex items-center gap-2 py-0.5">
            <div
              className="w-2.5 h-2.5 rounded-sm flex-shrink-0"
              style={{ backgroundColor: w.color }}
            />
            <span className="flex-1 text-gray-600 truncate">{w.wetland_type}</span>
            <span className="font-medium text-gray-500">{w.acres.toFixed(1)} ac</span>
          </div>
        ))}
      </div>
    </div>
  )
}
