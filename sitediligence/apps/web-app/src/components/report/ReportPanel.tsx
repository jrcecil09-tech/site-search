import { FileText, Download, Eye } from 'lucide-react'
import { useExport } from '@/hooks/useExport'
import { useState } from 'react'

const FORMATS = [
  { value: 'pdf',     label: 'PDF Report' },
  { value: 'docx',   label: 'Word Document' },
  { value: 'geojson',label: 'GeoJSON' },
  { value: 'dxf',    label: 'DXF / CAD' },
  { value: 'qgis',   label: 'QGIS Package' },
]

interface ReportPanelProps {
  siteId: string
}

export function ReportPanel({ siteId }: ReportPanelProps) {
  const [format, setFormat] = useState('pdf')
  const { create, status } = useExport()

  return (
    <div className="space-y-4 p-4">
      <div className="flex items-center gap-2">
        <FileText className="w-4 h-4 text-navy" />
        <span className="text-sm font-semibold text-slate">Generate Report</span>
      </div>

      <div className="space-y-2">
        <label className="text-xs text-gray-500 uppercase tracking-wide">Format</label>
        <select
          value={format}
          onChange={(e) => setFormat(e.target.value)}
          className="w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-1 focus:ring-navy"
        >
          {FORMATS.map((f) => (
            <option key={f.value} value={f.value}>{f.label}</option>
          ))}
        </select>
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => create.mutate({ site_id: siteId, format })}
          disabled={create.isPending}
          className="flex-1 flex items-center justify-center gap-1.5 bg-navy text-white text-sm py-2 rounded-md hover:bg-navy-600 transition-colors disabled:opacity-50"
        >
          <Download className="w-3.5 h-3.5" />
          {create.isPending ? 'Generating…' : 'Generate'}
        </button>
        <button className="px-3 py-2 border text-sm rounded-md hover:bg-gray-50 transition-colors">
          <Eye className="w-3.5 h-3.5 text-gray-500" />
        </button>
      </div>

      {status.data && (
        <p className="text-xs text-center text-gray-500">
          Status: <span className="font-medium">{status.data.status}</span>
        </p>
      )}
    </div>
  )
}
