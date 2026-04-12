import { CheckCircle, XCircle, Loader2, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'

type Status = 'pending' | 'loading' | 'success' | 'error' | 'no_data'

interface ModuleCardProps {
  title: string
  status: Status
  summary?: string
  featureCount?: number
  children?: React.ReactNode
}

const STATUS_CONFIG: Record<Status, { icon: typeof CheckCircle; color: string; label: string }> = {
  pending:  { icon: AlertCircle, color: 'text-gray-400',  label: 'Pending' },
  loading:  { icon: Loader2,     color: 'text-amber',     label: 'Loading' },
  success:  { icon: CheckCircle, color: 'text-green',     label: 'Complete' },
  error:    { icon: XCircle,     color: 'text-red-500',   label: 'Error' },
  no_data:  { icon: AlertCircle, color: 'text-gray-400',  label: 'No Data' },
}

export function ModuleCard({ title, status, summary, featureCount, children }: ModuleCardProps) {
  const [expanded, setExpanded] = useState(false)
  const cfg = STATUS_CONFIG[status]
  const Icon = cfg.icon

  return (
    <div className="border rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded((e) => !e)}
        className="w-full flex items-center gap-3 px-3 py-2.5 bg-white hover:bg-gray-50 transition-colors text-left"
      >
        <Icon className={cn('w-4 h-4 flex-shrink-0', cfg.color, status === 'loading' && 'animate-spin')} />
        <span className="flex-1 text-sm font-medium text-slate">{title}</span>
        {featureCount !== undefined && (
          <span className="text-xs bg-navy/10 text-navy px-1.5 py-0.5 rounded font-mono">
            {featureCount}
          </span>
        )}
        {children && (expanded ? <ChevronUp className="w-3.5 h-3.5 text-gray-400" /> : <ChevronDown className="w-3.5 h-3.5 text-gray-400" />)}
      </button>
      {summary && (
        <p className="px-3 pb-2 text-xs text-gray-500 bg-white">{summary}</p>
      )}
      {expanded && children && (
        <div className="border-t bg-gray-50 p-3">{children}</div>
      )}
    </div>
  )
}
