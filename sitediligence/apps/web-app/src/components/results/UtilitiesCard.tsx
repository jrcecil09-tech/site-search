import { Zap, Flame, Droplets, Wrench, Radio } from 'lucide-react'
import { cn } from '@/lib/utils'

// ── Types ──────────────────────────────────────────────────────────────────────

interface TransmissionLine {
  id: string | null
  owner: string | null
  voltage_kv: number | null
  type: string | null
  status: string | null
  color: string
  category: string
}

interface PlaceholderLayer {
  id: string
  name: string
  category: string
  color: string
  weight: number
  enabled: boolean
  note: string
  source: string | null
}

interface VoltageSummary {
  min_kv: number | null
  max_kv: number | null
  count: number
  classes: string[]
}

interface UtilitiesData {
  flag: boolean
  transmission_count: number
  transmission_lines: TransmissionLine[]
  voltage_summary: VoltageSummary
  placeholder_layers: PlaceholderLayer[]
  display: {
    color_transmission: string
    color_gas: string
    color_water: string
    color_sewer: string
    color_telecom: string
    buffer_miles: number
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────────

const CATEGORY_ICON: Record<string, React.ReactNode> = {
  electric:     <Zap      className="w-3 h-3" />,
  transmission: <Zap      className="w-3 h-3" />,
  gas:          <Flame    className="w-3 h-3" />,
  water:        <Droplets className="w-3 h-3" />,
  sewer:        <Wrench   className="w-3 h-3" />,
  telecom:      <Radio    className="w-3 h-3" />,
}

function LineSwatch({ color, weight = 2 }: { color: string; weight?: number }) {
  return (
    <span
      className="flex-shrink-0 rounded"
      style={{ display: 'inline-block', width: 16, height: weight * 1.5, backgroundColor: color }}
    />
  )
}

function CountTile({ color, label, value }: { color: string; label: string; value: string | number }) {
  return (
    <div className="rounded border bg-white p-2">
      <div className="flex items-center gap-1.5 mb-0.5">
        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
        <span className="text-gray-500 truncate">{label}</span>
      </div>
      <div className="font-bold text-lg text-slate">{value}</div>
    </div>
  )
}

// ── Main card ──────────────────────────────────────────────────────────────────

export function UtilitiesCard({ data }: { data: UtilitiesData }) {
  const { transmission_lines, voltage_summary, placeholder_layers, display } = data

  const colorFor: Record<string, string> = {
    electric:     display.color_transmission,
    transmission: display.color_transmission,
    gas:          display.color_gas,
    water:        display.color_water,
    sewer:        display.color_sewer,
    telecom:      display.color_telecom,
  }

  return (
    <div className="space-y-3 text-xs">

      {/* Summary tiles */}
      <div className="grid grid-cols-2 gap-1.5">
        <CountTile
          color={display.color_transmission}
          label="Transmission Lines"
          value={data.transmission_count}
        />
        <CountTile
          color={display.color_transmission}
          label="Max Voltage"
          value={
            voltage_summary.max_kv != null
              ? `${voltage_summary.max_kv.toLocaleString()} kV`
              : '—'
          }
        />
      </div>

      {/* Voltage class chips */}
      {voltage_summary.classes && voltage_summary.classes.length > 0 && (
        <div className="flex gap-1 flex-wrap">
          {voltage_summary.classes.map((cls) => (
            <span
              key={cls}
              className="px-1.5 py-0.5 rounded text-[10px] font-medium border"
              style={{
                backgroundColor: display.color_transmission + '18',
                color: '#92400e',
                borderColor: display.color_transmission + '55',
              }}
            >
              {cls}
            </span>
          ))}
        </div>
      )}

      {/* Transmission line list */}
      {transmission_lines.length > 0 && (
        <section>
          <div className="font-medium text-gray-500 mb-1">
            Lines Within {display.buffer_miles} mi
          </div>
          <div className="divide-y divide-gray-100">
            {transmission_lines.slice(0, 8).map((line, i) => (
              <div key={line.id ?? i} className="flex items-center gap-2 py-1.5">
                <LineSwatch color={line.color} weight={2.5} />
                <div className="flex-1 min-w-0">
                  <div className="text-gray-700 truncate font-medium">
                    {line.owner ?? 'Unknown Operator'}
                  </div>
                  <div className="text-gray-400 text-[10px]">
                    {[
                      line.voltage_kv ? `${line.voltage_kv.toLocaleString()} kV` : null,
                      line.type,
                      line.status && line.status.toLowerCase() !== 'in service'
                        ? line.status
                        : null,
                    ]
                      .filter(Boolean)
                      .join(' · ')}
                  </div>
                </div>
              </div>
            ))}
          </div>
          {transmission_lines.length > 8 && (
            <div className="text-gray-400 text-right mt-1">
              +{transmission_lines.length - 8} more lines
            </div>
          )}
        </section>
      )}

      {/* Other utility layers — placeholder cards */}
      <section>
        <div className="font-medium text-gray-500 mb-1">Other Utility Layers</div>
        <div className="space-y-1">
          {placeholder_layers.map((layer) => {
            const color = colorFor[layer.category] ?? '#888888'
            return (
              <div
                key={layer.id}
                className={cn(
                  'flex items-start gap-2 py-1.5 px-2 rounded border',
                  layer.enabled
                    ? 'bg-white border-gray-200'
                    : 'bg-gray-50 border-dashed border-gray-200',
                )}
              >
                <span className="flex-shrink-0 mt-0.5" style={{ color }}>
                  {CATEGORY_ICON[layer.category] ?? <Wrench className="w-3 h-3" />}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-1">
                    <span
                      className={cn(
                        'font-medium truncate',
                        layer.enabled ? 'text-gray-700' : 'text-gray-500',
                      )}
                    >
                      {layer.name}
                    </span>
                    <span
                      className={cn(
                        'text-[10px] flex-shrink-0 px-1 py-0.5 rounded',
                        layer.enabled
                          ? 'bg-green-50 text-green-700'
                          : 'bg-gray-100 text-gray-400',
                      )}
                    >
                      {layer.enabled ? 'Active' : 'Not configured'}
                    </span>
                  </div>
                  {!layer.enabled && layer.note && (
                    <div className="text-[10px] text-gray-400 leading-snug mt-0.5 line-clamp-2">
                      {layer.note}
                    </div>
                  )}
                  {layer.enabled && layer.source && (
                    <div className="text-[10px] text-gray-400 mt-0.5">{layer.source}</div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </section>

      <div className="text-gray-400 text-right">
        Within {display.buffer_miles} mi · HIFLD / EIA
      </div>
    </div>
  )
}
