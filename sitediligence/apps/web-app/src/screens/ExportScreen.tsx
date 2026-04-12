import { useState } from 'react'
import { Download, FileText, Map, Code, Package } from 'lucide-react'
import { ReportPreview } from '@/components/report/ReportPreview'
import { useExportFormats } from '@/hooks/useExport'
import { cn } from '@/lib/utils'

const FORMAT_META: Record<string, { icon: typeof FileText; desc: string }> = {
  pdf:      { icon: FileText, desc: 'Multi-page PDF with maps and tables' },
  docx:     { icon: FileText, desc: 'Editable Word document' },
  geojson:  { icon: Code,     desc: 'All layers as a single GeoJSON file' },
  kml:      { icon: Map,      desc: 'Google Earth compatible KML' },
  dxf:      { icon: Package,  desc: 'AutoCAD / BricsCAD DXF' },
  qgis:     { icon: Map,      desc: 'QGIS project with all layers' },
  arcgis:   { icon: Map,      desc: 'Shapefile package for ArcGIS' },
  shapefile:{ icon: Package,  desc: 'ESRI Shapefile zip' },
}

export default function ExportScreen() {
  const [selected, setSelected] = useState('pdf')
  const { data: formats = [] } = useExportFormats()

  return (
    <div className="flex h-full">
      {/* Left: format picker */}
      <div className="w-72 border-r bg-white overflow-y-auto flex-shrink-0">
        <div className="px-4 py-3 border-b">
          <h1 className="text-sm font-bold text-slate">Export</h1>
          <p className="text-xs text-gray-500">Choose a format for your site report</p>
        </div>
        <div className="p-3 space-y-1.5">
          {(formats.length ? formats : Object.keys(FORMAT_META)).map((fmt) => {
            const meta = FORMAT_META[fmt] ?? { icon: Download, desc: '' }
            const Icon = meta.icon
            return (
              <button
                key={fmt}
                onClick={() => setSelected(fmt)}
                className={cn(
                  'w-full flex items-center gap-3 p-3 rounded-lg text-left transition-all',
                  selected === fmt
                    ? 'bg-navy text-white'
                    : 'hover:bg-gray-50 text-slate',
                )}
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <div>
                  <p className="text-xs font-semibold uppercase">{fmt}</p>
                  <p className={cn('text-[10px]', selected === fmt ? 'text-white/70' : 'text-gray-400')}>
                    {meta.desc}
                  </p>
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {/* Right: preview + generate */}
      <div className="flex-1 flex flex-col p-6 gap-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate uppercase">{selected} Export</h2>
            <p className="text-xs text-gray-500">{FORMAT_META[selected]?.desc}</p>
          </div>
          <button className="flex items-center gap-1.5 bg-navy text-white text-sm px-4 py-2 rounded-md hover:bg-navy-600 transition-colors">
            <Download className="w-4 h-4" />
            Generate
          </button>
        </div>
        <div className="flex-1 min-h-0">
          <ReportPreview format={selected} />
        </div>
      </div>
    </div>
  )
}
