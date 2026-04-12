import { ModuleCard } from './ModuleCard'
import { FindingsSummary } from './FindingsSummary'
import { RefreshCw } from 'lucide-react'

interface ResultItem {
  id: string
  title: string
  status: 'pending' | 'loading' | 'success' | 'error' | 'no_data'
  summary?: string
  featureCount?: number
  children?: React.ReactNode
}

interface ResultsPanelProps {
  results: ResultItem[]
  onRerun?: () => void
}

export function ResultsPanel({ results, onRerun }: ResultsPanelProps) {
  const complete = results.filter((r) => r.status === 'success' || r.status === 'no_data')
  const findings = results.filter((r) => r.status === 'success' && (r.featureCount ?? 0) > 0)

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2 border-b bg-white">
        <span className="text-xs font-semibold text-slate uppercase tracking-wide">
          Query Results
        </span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">{complete.length}/{results.length} complete</span>
          {onRerun && (
            <button onClick={onRerun} className="text-navy hover:text-navy-700 transition-colors">
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {findings.length > 0 && (
        <div className="p-3 border-b bg-amber/5">
          <FindingsSummary findings={findings} />
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
        {results.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-gray-400">
            <p className="text-sm">No results yet</p>
            <p className="text-xs mt-1">Select a site and run queries</p>
          </div>
        ) : (
          results.map((r) => (
            <ModuleCard
              key={r.id}
              title={r.title}
              status={r.status}
              summary={r.summary}
              featureCount={r.featureCount}
            >
              {r.children}
            </ModuleCard>
          ))
        )}
      </div>
    </div>
  )
}
