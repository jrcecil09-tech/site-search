import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, MapPin, FileText, Loader2 } from 'lucide-react'
import { useProjectStore } from '@/store/projectStore'
import { useMapStore, EpaMarker, HistoricMarker } from '@/store/mapStore'
import { SiteMap } from '@/components/map/SiteMap'
import { ResultsPanel } from '@/components/results/ResultsPanel'
import { WetlandsSummaryCard } from '@/components/results/WetlandsSummaryCard'
import { FloodZonesSummaryCard } from '@/components/results/FloodZonesSummaryCard'
import { StreamsSummaryCard } from '@/components/results/StreamsSummaryCard'
import { ElevationSummaryCard } from '@/components/results/ElevationSummaryCard'
import { SoilsSummaryCard } from '@/components/results/SoilsSummaryCard'
import { EpaSummaryCard } from '@/components/results/EpaSummaryCard'
import { HistoricSummaryCard } from '@/components/results/HistoricSummaryCard'
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

    if (r.query_type === 'streams') {
      const d = r.data
      const hasStreams = d?.streams_present === true
      const total = (d?.flowline_count ?? 0) + (d?.waterbody_count ?? 0)
      return {
        id: 'streams',
        title: 'NHD Streams',
        status: r.status === 'success' ? (hasStreams ? 'success' : 'no_data') : 'error',
        summary: hasStreams
          ? `${d.flowline_count} flowlines · ${d.summary.total_length_km.toFixed(1)} km · max order ${d.summary.max_stream_order}`
          : `No streams within ${d?.buffer_ft ?? 500} ft`,
        featureCount: total,
        children: hasStreams ? <StreamsSummaryCard data={d} /> : undefined,
      }
    }

    if (r.query_type === 'epa') {
      const d = r.data
      const hasData = (d?.summary?.frs_count ?? 0) + (d?.summary?.superfund_count ?? 0) +
                      (d?.summary?.rcra_count ?? 0) + (d?.summary?.tri_count ?? 0) > 0
      const sfNear  = d?.summary?.superfund_near_count ?? 0
      const viol    = d?.summary?.echo_violations ?? 0
      return {
        id: 'epa',
        title: 'EPA Records',
        status: r.status === 'success' ? (hasData ? 'success' : 'no_data') : 'error',
        summary: hasData
          ? [
              d.summary.superfund_count > 0 && `${d.summary.superfund_count} Superfund${sfNear > 0 ? ` (${sfNear} near)` : ''}`,
              d.summary.rcra_count > 0      && `${d.summary.rcra_count} RCRA`,
              d.summary.tri_count > 0       && `${d.summary.tri_count} TRI`,
              viol > 0                      && `${viol} violation${viol !== 1 ? 's' : ''}`,
            ].filter(Boolean).join(' · ')
          : 'No EPA records found',
        featureCount: (d?.summary?.frs_count ?? 0) + (d?.summary?.superfund_count ?? 0),
        children: hasData ? <EpaSummaryCard data={d} /> : undefined,
      }
    }

    if (r.query_type === 'soils') {
      const d = r.data
      const hasUnits = (d?.map_unit_count ?? 0) > 0
      const hydric   = d?.hydric_present === true
      return {
        id: 'soils',
        title: 'SSURGO Soils',
        status: r.status === 'success' ? (hasUnits ? 'success' : 'no_data') : 'error',
        summary: hasUnits
          ? `${d.map_unit_count} map units${hydric ? ' · Hydric soils present' : ''}`
          : 'No soil data found',
        featureCount: d?.map_unit_count,
        children: hasUnits ? <SoilsSummaryCard data={d} /> : undefined,
      }
    }

    if (r.query_type === 'elevation') {
      const d = r.data
      const ft = d?.centroid_elevation_ft
      const relief = d?.stats?.relief_ft
      return {
        id: 'elevation',
        title: '3DEP Elevation',
        status: r.status === 'success' ? (ft !== null ? 'success' : 'no_data') : 'error',
        summary: ft !== null
          ? `${ft?.toFixed(0)} ft · ${d?.centroid_elevation_m?.toFixed(0)} m · relief ${relief?.toFixed(0)} ft`
          : 'No elevation data',
        featureCount: d?.sample_count,
        children: ft !== null ? <ElevationSummaryCard data={d} /> : undefined,
      }
    }

    if (r.query_type === 'historic') {
      const d = r.data
      const nrhpCount = d?.summary?.nrhp_count ?? 0
      const cemCount  = d?.summary?.cemetery_count ?? 0
      const nrhpNear  = d?.summary?.nrhp_near_count ?? 0
      const cemNear   = d?.summary?.cemetery_near_count ?? 0
      const hasData   = nrhpCount + cemCount > 0
      const flagFt    = d?.display?.flag_distance_ft ?? 500
      return {
        id: 'historic',
        title: 'Historic & Archaeological',
        status: r.status === 'success' ? (hasData ? 'success' : 'no_data') : 'error',
        summary: hasData
          ? [
              nrhpCount > 0 && `${nrhpCount} NRHP${nrhpNear > 0 ? ` (${nrhpNear} within ${flagFt} ft)` : ''}`,
              cemCount  > 0 && `${cemCount} cemetery${cemCount !== 1 ? 's' : ''}${cemNear > 0 ? ` (${cemNear} adj.)` : ''}`,
            ].filter(Boolean).join(' · ')
          : 'No NRHP properties or cemeteries found',
        featureCount: nrhpCount + cemCount,
        children: hasData ? <HistoricSummaryCard data={d} /> : undefined,
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

  const setCenter           = useMapStore((s) => s.setCenter)
  const setZoom             = useMapStore((s) => s.setZoom)
  const toggleLayer         = useMapStore((s) => s.toggleLayer)
  const layers              = useMapStore((s) => s.layers)
  const setEpaMarkers       = useMapStore((s) => s.setEpaMarkers)
  const clearEpaMarkers     = useMapStore((s) => s.clearEpaMarkers)
  const setHistoricMarkers  = useMapStore((s) => s.setHistoricMarkers)
  const clearHistoricMarkers = useMapStore((s) => s.clearHistoricMarkers)

  async function handleRunQueries() {
    if (loading) return
    setLoading(true)
    clearEpaMarkers()
    clearHistoricMarkers()
    setResults([
      { id: 'wetlands',    title: 'NWI Wetlands',              status: 'loading' },
      { id: 'flood_zones', title: 'FEMA Flood Zones',           status: 'loading' },
      { id: 'streams',     title: 'NHD Streams',                status: 'loading' },
      { id: 'soils',       title: 'SSURGO Soils',               status: 'loading' },
      { id: 'epa',         title: 'EPA Records',                status: 'loading' },
      { id: 'elevation',   title: '3DEP Elevation',             status: 'loading' },
      { id: 'historic',    title: 'Historic & Archaeological',  status: 'loading' },
    ])

    try {
      const res = await api.get('/api/v1/queries/demo')
      const items = buildResultItems(res.data.results)
      setResults(items)

      // Pan map to demo site bbox center
      const bbox = res.data.bbox as [number, number, number, number]
      const lat = (bbox[1] + bbox[3]) / 2
      const lon = (bbox[0] + bbox[2]) / 2
      setCenter([lat, lon])
      setZoom(13)

      // Enable map overlays for returned query types
      const returnedTypes = new Set(res.data.results.map((r: any) => r.query_type))
      const wetlandsVisible  = layers.find((l) => l.id === 'wetlands')?.visible
      const floodVisible     = layers.find((l) => l.id === 'flood')?.visible
      const streamsVisible   = layers.find((l) => l.id === 'streams')?.visible
      const soilsVisible     = layers.find((l) => l.id === 'soils')?.visible
      const epaVisible       = layers.find((l) => l.id === 'epa')?.visible
      const historicVisible  = layers.find((l) => l.id === 'historic')?.visible
      if (returnedTypes.has('wetlands')    && !wetlandsVisible) toggleLayer('wetlands')
      if (returnedTypes.has('flood_zones') && !floodVisible)    toggleLayer('flood')
      if (returnedTypes.has('streams')     && !streamsVisible)  toggleLayer('streams')
      if (returnedTypes.has('soils')       && !soilsVisible)    toggleLayer('soils')
      if (returnedTypes.has('epa')         && !epaVisible)      toggleLayer('epa')
      if (returnedTypes.has('historic')    && !historicVisible) toggleLayer('historic')

      // Build EPA point markers
      const epaResult = res.data.results.find((r: any) => r.query_type === 'epa')
      if (epaResult?.status === 'success' && epaResult.data) {
        const d = epaResult.data
        const markers: EpaMarker[] = [
          ...(d.superfund_sites  || []).filter((s: any) => s.lat && s.lon).map((s: any) => ({
            lat: s.lat, lon: s.lon, name: s.name,
            category: 'superfund' as const, color: d.display.color_superfund,
            detail: s.distance_miles != null ? `${s.distance_miles.toFixed(2)} mi from site` : undefined,
          })),
          ...(d.rcra_handlers    || []).filter((r: any) => r.lat && r.lon).map((r: any) => ({
            lat: r.lat, lon: r.lon, name: r.name,
            category: 'rcra' as const, color: d.display.color_rcra,
          })),
          ...(d.tri_facilities   || []).filter((t: any) => t.lat && t.lon).map((t: any) => ({
            lat: t.lat, lon: t.lon, name: t.name,
            category: 'tri' as const, color: d.display.color_tri,
            detail: t.sic_code ? `SIC ${t.sic_code}` : undefined,
          })),
          ...(d.frs_facilities   || []).filter((f: any) => f.lat && f.lon).map((f: any) => ({
            lat: f.lat, lon: f.lon, name: f.name,
            category: 'frs' as const, color: d.display.color_frs,
            detail: (f.programs || []).join(', ') || undefined,
          })),
        ]
        setEpaMarkers(markers)
      }

      // Build historic point markers
      const historicResult = res.data.results.find((r: any) => r.query_type === 'historic')
      if (historicResult?.status === 'success' && historicResult.data) {
        const d = historicResult.data
        const markers: HistoricMarker[] = [
          ...(d.nrhp_properties || []).filter((p: any) => p.lat && p.lon).map((p: any) => ({
            lat:       p.lat,
            lon:       p.lon,
            name:      p.name,
            category:  'nrhp' as const,
            color:     d.display.color_nrhp,
            detail:    [p.category, p.date_listed ? `Listed ${p.date_listed.slice(0, 4)}` : null]
                         .filter(Boolean).join(' · ') || undefined,
            near_flag: p.near_flag ?? false,
          })),
          ...(d.cemeteries || []).filter((c: any) => c.lat && c.lon).map((c: any) => ({
            lat:       c.lat,
            lon:       c.lon,
            name:      c.name,
            category:  'cemetery' as const,
            color:     d.display.color_cemetery,
            detail:    c.gnis_id ? `GNIS ${c.gnis_id}` : undefined,
            near_flag: c.near_flag ?? false,
          })),
        ]
        setHistoricMarkers(markers)
      }
    } catch {
      setResults([
        { id: 'wetlands',    title: 'NWI Wetlands',             status: 'error', summary: 'Query failed' },
        { id: 'flood_zones', title: 'FEMA Flood Zones',          status: 'error', summary: 'Query failed' },
        { id: 'streams',     title: 'NHD Streams',               status: 'error', summary: 'Query failed' },
        { id: 'soils',       title: 'SSURGO Soils',              status: 'error', summary: 'Query failed' },
        { id: 'epa',         title: 'EPA Records',               status: 'error', summary: 'Query failed' },
        { id: 'elevation',   title: '3DEP Elevation',            status: 'error', summary: 'Query failed' },
        { id: 'historic',    title: 'Historic & Archaeological', status: 'error', summary: 'Query failed' },
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
