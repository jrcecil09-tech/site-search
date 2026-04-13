interface StreamsData {
  flowline_count: number
  waterbody_count: number
  buffer_ft: number
  streams: Array<{
    name: string | null
    feature_type: string
    stream_order: number
    length_km: number
    color: string
  }>
  waterbodies: Array<{
    name: string | null
    feature_type: string
    area_sqkm: number
    color: string
  }>
  summary: {
    total_length_km: number
    max_stream_order: number
    stream_orders_present: number[]
    named_streams: string[]
    named_waterbodies: string[]
    by_type: Record<string, number>
    high_order_stream: boolean
  }
}

interface StreamsSummaryCardProps {
  data: StreamsData
}

const ORDER_LABEL: Record<number, string> = {
  1: '1st (headwater)',
  2: '2nd',
  3: '3rd',
  4: '4th',
  5: '5th',
  6: '6th (medium river)',
  7: '7th (large river)',
  8: '8th',
  9: '9th',
  10: '10th',
}

export function StreamsSummaryCard({ data }: StreamsSummaryCardProps) {
  const { summary } = data

  return (
    <div className="space-y-3 text-xs">
      <div className="flex flex-wrap gap-1.5">
        {summary.high_order_stream ? (
          <span className="font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-700">
            Order {summary.max_stream_order} Stream
          </span>
        ) : (
          <span className="font-bold px-2 py-0.5 rounded bg-gray-100 text-gray-600">
            Headwater Streams
          </span>
        )}
        <span className="px-2 py-0.5 rounded bg-sky-50 text-sky-700">
          {data.buffer_ft} ft buffer
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div className="bg-white rounded p-2 border">
          <div className="text-gray-500">Flowlines</div>
          <div className="text-sm font-semibold mt-0.5">{data.flowline_count}</div>
          <div className="text-gray-400">{summary.total_length_km.toFixed(1)} km total</div>
        </div>
        <div className="bg-white rounded p-2 border">
          <div className="text-gray-500">Max Stream Order</div>
          <div className="text-sm font-semibold mt-0.5">{summary.max_stream_order}</div>
          <div className="text-gray-400">
            {ORDER_LABEL[summary.max_stream_order] ?? `Order ${summary.max_stream_order}`}
          </div>
        </div>
      </div>

      {summary.named_streams.length > 0 && (
        <div>
          <div className="text-gray-500 font-medium mb-1">Named Streams</div>
          {summary.named_streams.map((name) => (
            <div key={name} className="flex items-center gap-1.5 py-0.5">
              <div className="w-2 h-0.5 bg-blue-700 flex-shrink-0 rounded" />
              <span className="text-gray-700">{name}</span>
            </div>
          ))}
        </div>
      )}

      {data.streams.length > 0 && (
        <div>
          <div className="text-gray-500 font-medium mb-1">Top Flowlines</div>
          {data.streams.slice(0, 6).map((s, i) => (
            <div
              key={i}
              className="flex items-center gap-2 py-0.5 border-b border-gray-100 last:border-0"
            >
              <div
                className="w-2.5 h-2.5 rounded-sm flex-shrink-0"
                style={{ backgroundColor: s.color }}
              />
              <span className="flex-1 text-gray-600 truncate">
                {s.name ?? `Unnamed (order ${s.stream_order})`}
              </span>
              <span className="text-gray-400 flex-shrink-0">{s.length_km.toFixed(1)} km</span>
            </div>
          ))}
        </div>
      )}

      {summary.named_waterbodies.length > 0 && (
        <div>
          <div className="text-gray-500 font-medium mb-1">Water Bodies</div>
          {summary.named_waterbodies.map((name) => (
            <div key={name} className="flex items-center gap-1.5 py-0.5">
              <div className="w-2.5 h-2.5 rounded-sm flex-shrink-0 bg-sky-300 border border-sky-400" />
              <span className="text-gray-700">{name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
