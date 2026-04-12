import { AlertTriangle } from 'lucide-react'

interface Finding {
  id: string
  title: string
  featureCount?: number
}

interface FindingsSummaryProps {
  findings: Finding[]
}

export function FindingsSummary({ findings }: FindingsSummaryProps) {
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-1.5">
        <AlertTriangle className="w-3.5 h-3.5 text-amber" />
        <span className="text-xs font-semibold text-amber">
          {findings.length} module{findings.length !== 1 ? 's' : ''} with findings
        </span>
      </div>
      <div className="flex flex-wrap gap-1">
        {findings.map((f) => (
          <span
            key={f.id}
            className="text-[10px] bg-amber/20 text-amber-700 px-1.5 py-0.5 rounded font-medium"
          >
            {f.title}{f.featureCount ? ` (${f.featureCount})` : ''}
          </span>
        ))}
      </div>
    </div>
  )
}
