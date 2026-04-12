import { useState } from 'react'
import { Pencil, Square, Circle, Minus } from 'lucide-react'
import { cn } from '@/lib/utils'

type DrawMode = 'none' | 'point' | 'rectangle' | 'circle' | 'polyline'

interface DrawToolProps {
  onModeChange?: (mode: DrawMode) => void
}

const TOOLS: { mode: DrawMode; icon: typeof Pencil; label: string }[] = [
  { mode: 'point',     icon: Pencil,  label: 'Point' },
  { mode: 'rectangle', icon: Square,  label: 'Rectangle' },
  { mode: 'circle',    icon: Circle,  label: 'Circle' },
  { mode: 'polyline',  icon: Minus,   label: 'Line' },
]

export function DrawTool({ onModeChange }: DrawToolProps) {
  const [activeMode, setActiveMode] = useState<DrawMode>('none')

  const toggle = (mode: DrawMode) => {
    const next = activeMode === mode ? 'none' : mode
    setActiveMode(next)
    onModeChange?.(next)
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-1.5 flex flex-col gap-1">
      {TOOLS.map(({ mode, icon: Icon, label }) => (
        <button
          key={mode}
          title={label}
          onClick={() => toggle(mode)}
          className={cn(
            'w-8 h-8 flex items-center justify-center rounded transition-all',
            activeMode === mode
              ? 'bg-navy text-white'
              : 'text-gray-500 hover:bg-gray-100',
          )}
        >
          <Icon className="w-4 h-4" />
        </button>
      ))}
    </div>
  )
}
