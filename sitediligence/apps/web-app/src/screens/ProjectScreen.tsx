import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, MapPin, FileText, Loader2 } from 'lucide-react'
import { useProjectStore } from '@/store/projectStore'
import { useMapStore } from '@/store/mapStore'
import { SiteMap } from '@/components/map/SiteMap'
import { ResultsPanel } from '@/components/results/ResultsPanel'
import { WetlandsSummaryCard } from '@/components/results/WetlandsSummaryCard'
import { FloodZonesSummaryCard } from '@/components/results/FloodZonesSummaryCard'
import { api } from '@/services/api'

interface ResultItem {
  id: string
  title: string
  status: 'pending' | 'loading' | 'success' | 'error' | 'no_data'
  summary?: string
  featureCount?: number
  children?: React.ReactNode
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function buildResultItems(apiResults: any[]): ResultItem[] {
  return apiResults.map((r) => {
    if (r.query_type === 'wetlands') {
      const d = r.data
      const hasWetlands = d?.wetlands_present === true
      return {
        id: 'wetlands',
        title: 'NWI Wetlands',
        status: r.status === 'success' ? (hasWetlands ? 'success' : 'no_data') : 'error',
        summary: hasWetlands
          ? `${d.wetland_count} features · ${d.total_wetland_acres.toFixed(1)} ac · CWA §404 regulated`
          : 'No wetlands found within 1 mile',
        featureCount: d?.wetland_count,
        children: hasWetlands ? <WetlandsSummaryCard data={d} /> : undefined,
      }
    }

    if (r.query_type === 'flood_zones') {
      const d = r.data
      const hasSFHA = d?.sfha_present === true
      const hasZones = (d?.zone_count ?? 0) > 0
      return {
        id: 'flood_zones',
        title: 'FEMA Flood Zones',
        status: r.status === 'success' ? (hasZones ? 'success' : 'no_data') : 'error',
        summary: hasSFHA
          ? `Zone ${d.summary.zones_found.join(', ')} · SFHA present${d.summary.bfe_range_ft ? ` · BFE ${d.summary.bfe_range_ft.min} ft` : ''}`
          : hasZones
            ? `Zone ${d.summary.zones_found.join(', ')} · No SFHA`
            : 'No flood zones found',
        featureCount: d?.zone_count,
        children: hasZones ? <FloodZonesSummaryCard data={d} /> : undefined,
      }
    }

    return {
      id: r.query_type,
      title: r.query_type,
      status: r.status === 'success' ? 'success' : 'error',
      summary: r.error ?? undefined,
    }
  })
}

export default function ProjectScreen() {
  const { id } = useParams<{ id: string }>()
  const project = useProjectStore((s) => s.projects.find((p) => p.id === id))
  const [results, setResults] = useState<ResultItem[]>([])
  const [loading, setLoading] = useState(false)

  const setCenter  = useMapStore((s) => s.setCenter)
  const setZoom    = useMapStore((s) => s.setZoom)
  const toggleLayer = useMapStore((s) => s.toggleLayer)
  const layers     = useMapStore((s) => s.layers)

  async function handleRunQueries() {
    if (loading) return
    setLoading(true)
    setResults([
      { id: 'wetlands',    title: 'NWI Wetlands',     status: 'loading' },
      { id: 'flood_zones', title: 'FEMA Flood Zones',  status: 'loading' },
    ])

    try {
      const res = await api.get('/api/v1/queries/demo')
      const items = buildResultItems(res.data.results)
      setResults(items)

      // Pan map to Louisiana demo site
      setCenter([30.0, -90.0])
      setZoom(12)

      // Enable map overlays if they are currently hidden
      const wetlandsVisible = layers.find((l) => l.id === 'wetlands')?.visible
      const floodVisible    = layers.find((l) => l.id === 'flood')?.visible
      if (!wetlandsVisible) toggleLayer('wetlands')
      if (!floodVisible)    toggleLayer('flood')
    } catch {
      setResults([
        { id: 'wetlands',    title: 'NWI Wetlands',    status: 'error', summary: 'Query failed' },
        { id: 'flood_zones', title: 'FEMA Flood Zones', status: 'error', summary: 'Query failed' },
      ])
    } finally {
      setLoading(false)
    }
  }

  if (!project) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3">
        <p className="text-gray-500">Project not found</p>
        <Link to="/dashboard" className="text-navy text-sm hover:underline">
          ← Back to Dashboard
        </Link>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 px-5 py-3 border-b bg-white">
        <Link to="/dashboard" className="text-gray-400 hover:text-gray-600 transition-colors">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div className="flex-1">
          <h1 className="text-sm font-bold text-slate">{project.name}</h1>
          <p className="text-xs text-gray-400">
            {project.status} · {project.tags.join(', ') || 'no tags'}
          </p>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 relative">
          <SiteMap className="w-full h-full" />
          <div className="absolute bottom-4 left-4 z-10 flex gap-2">
            <button className="flex items-center gap-1.5 bg-navy text-white text-xs px-3 py-1.5 rounded-md shadow hover:bg-navy-600 transition-colors">
              <MapPin className="w-3 h-3" /> Add Site
            </button>
            <button
              onClick={handleRunQueries}
              disabled={loading}
              className="flex items-center gap-1.5 bg-white border text-xs px-3 py-1.5 rounded-md shadow hover:bg-gray-50 transition-colors disabled:opacity-60"
            >
              {loading
                ? <Loader2 className="w-3 h-3 text-gray-500 animate-spin" />
                : <FileText className="w-3 h-3 text-gray-500" />}
              {loading ? 'Running…' : 'Run Queries'}
            </button>
          </div>
        </div>
        <div className="w-72 border-l flex-shrink-0">
          <ResultsPanel results={results} onRerun={handleRunQueries} />
        </div>
      </div>
    </div>
  )
}
