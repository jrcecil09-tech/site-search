import { Layers } from 'lucide-react'
import { useMapStore } from '@/store/mapStore'
import { cn } from '@/lib/utils'

export function LayerToggle() {
  const layers = useMapStore((s) => s.layers)
  const toggleLayer = useMapStore((s) => s.toggleLayer)

  const categories = [...new Set(layers.map((l) => l.category))]

  return (
    <div className="bg-white rounded-lg shadow-md p-3 min-w-48">
      <div className="flex items-center gap-1.5 mb-3">
        <Layers className="w-3.5 h-3.5 text-navy" />
        <span className="text-xs font-semibold text-slate uppercase tracking-wide">Layers</span>
      </div>
      {categories.map((cat) => (
        <div key={cat} className="mb-2">
          <p className="text-[10px] text-gray-400 uppercase tracking-wider mb-1">{cat}</p>
          {layers
            .filter((l) => l.category === cat)
            .map((layer) => (
              <label key={layer.id} className="flex items-center gap-2 py-0.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={layer.visible}
                  onChange={() => toggleLayer(layer.id)}
                  className="accent-navy w-3 h-3"
                />
                <span className={cn('text-xs', layer.visible ? 'text-slate' : 'text-gray-400')}>
                  {layer.name}
                </span>
              </label>
            ))}
        </div>
      ))}
    </div>
  )
}
