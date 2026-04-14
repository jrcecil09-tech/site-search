import { useState } from 'react'
import { AlertTriangle, ChevronDown, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

// ── Types ──────────────────────────────────────────────────────────────────────

interface NlcdClass {
  code: number
  name: string
  group: string
  color: string
  count: number
  pct: number
}

interface NlcdClassDef {
  code: number
  name: string
  group: string
  color: string
}

interface LandCoverData {
  flag: boolean
  review: boolean
  dominant_class: number | null
  dominant_name: string | null
  dominant_color: string | null
  dominant_pct: number | null
  sample_count: number
  grid_size: number
  class_breakdown: NlcdClass[]
  group_summary: Record<string, number>
  all_classes: NlcdClassDef[]
  display: {
    wms_url: string
    wms_layer: string
    opacity: number
    flag_classes: number[]
    note?: string
  }
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function ClassBar({ c }: { c: NlcdClass }) {
  return (
    <div className="flex items-center gap-2">
      <span
        className="w-2.5 h-2.5 rounded-sm flex-shrink-0 border border-black/10"
        style={{ backgroundColor: c.color }}
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-1">
          <span className="truncate text-gray-700 text-[11px]">{c.name}</span>
          <span className="text-gray-400 flex-shrink-0 font-mono text-[10px]">
            {c.pct.toFixed(1)}%
          </span>
        </div>
        <div className="h-1 rounded-full mt-0.5 bg-gray-100 overflow-hidden">
          <div
            className="h-full rounded-full"
            style={{ backgroundColor: c.color, width: `${c.pct}%` }}
          />
        </div>
      </div>
    </div>
  )
}

// Full NLCD legend — collapsible, grouped by category
function NlcdLegend({ classes }: { classes: NlcdClassDef[] }) {
  const [open, setOpen] = useState(false)

  // Group classes by group name
  const grouped: Record<string, NlcdClassDef[]> = {}
  for (const c of classes) {
    if (!grouped[c.group]) grouped[c.group] = []
    grouped[c.group].push(c)
  }

  return (
    <div className="border rounded overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
      >
        <div>
          <div className="font-medium text-gray-700 text-xs">NLCD 2021 Full Legend</div>
          <div className="text-[10px] text-gray-400 mt-0.5">
            {classes.length} classes · click to expand
          </div>
        </div>
        {open
          ? <ChevronDown className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
          : <ChevronRight className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />}
      </button>

      {open && (
        <div className="p-2 bg-white space-y-2">
          {Object.entries(grouped).map(([group, items]) => (
            <div key={group}>
              <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1">
                {group}
              </div>
              <div className="space-y-1">
                {items.map((c) => (
                  <div key={c.code} className="flex items-center gap-1.5">
                    <span
                      className="w-3 h-3 rounded-sm flex-shrink-0 border border-black/10"
                      style={{ backgroundColor: c.color }}
                    />
                    <span className="text-[11px] text-gray-600">
                      <span className="font-mono text-gray-400 mr-1">{c.code}</span>
                      {c.name}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Main card ──────────────────────────────────────────────────────────────────

export function LandCoverCard({ data }: { data: LandCoverData }) {
  const { class_breakdown, display, sample_count, grid_size } = data

  return (
    <div className="space-y-3 text-xs">

      {/* Flag banner — wetlands detected */}
      {data.flag && display.note && (
        <div className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded p-2">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0 mt-0.5" />
          <p className="text-amber-800 font-medium leading-snug">{display.note}</p>
        </div>
      )}

      {/* Dominant class tile */}
      {data.dominant_name && (
        <div className="flex items-center gap-2.5 p-2.5 bg-white border rounded">
          <span
            className="w-5 h-5 rounded flex-shrink-0 border border-black/10"
            style={{ backgroundColor: data.dominant_color ?? '#888' }}
          />
          <div>
            <div className="font-semibold text-slate">{data.dominant_name}</div>
            <div className="text-gray-400 text-[11px] mt-0.5">
              Dominant class · {data.dominant_pct?.toFixed(1)}% of {sample_count} samples
            </div>
          </div>
          {data.dominant_class !== null && (
            <span className="ml-auto font-mono text-[10px] text-gray-300 flex-shrink-0">
              #{data.dominant_class}
            </span>
          )}
        </div>
      )}

      {/* Class breakdown bars */}
      {class_breakdown.length > 0 && (
        <section>
          <div className="font-medium text-gray-500 mb-1.5">Land Cover Breakdown</div>
          <div className="space-y-1.5">
            {class_breakdown.map((c) => (
              <ClassBar key={c.code} c={c} />
            ))}
          </div>
        </section>
      )}

      {/* Group summary chips */}
      {Object.keys(data.group_summary).length > 1 && (
        <div className="flex flex-wrap gap-1">
          {Object.entries(data.group_summary)
            .sort(([, a], [, b]) => b - a)
            .map(([group, count]) => (
              <span
                key={group}
                className="px-1.5 py-0.5 rounded text-[10px] bg-gray-100 text-gray-600"
              >
                {group} ({count})
              </span>
            ))}
        </div>
      )}

      {/* Full legend (collapsible) */}
      {data.all_classes.length > 0 && (
        <NlcdLegend classes={data.all_classes} />
      )}

      <div className="text-gray-400 text-right">
        {grid_size}×{grid_size} grid · NLCD 2021 · MRLC
      </div>
    </div>
  )
}
