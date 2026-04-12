import { FileText } from 'lucide-react'

interface ReportPreviewProps {
  siteName?: string
  format?: string
}

export function ReportPreview({ siteName = 'Untitled Site', format = 'pdf' }: ReportPreviewProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-3 text-gray-400 bg-gray-50 rounded-lg border-2 border-dashed">
      <FileText className="w-12 h-12" />
      <div className="text-center">
        <p className="text-sm font-medium text-gray-600">{siteName}</p>
        <p className="text-xs uppercase tracking-wide mt-0.5">{format.toUpperCase()} Preview</p>
      </div>
      <p className="text-xs text-gray-400">Generate a report to see the preview here</p>
    </div>
  )
}
