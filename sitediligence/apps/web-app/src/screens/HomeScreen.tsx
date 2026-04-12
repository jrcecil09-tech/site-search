import { useState } from 'react'
import { SiteMap } from '@/components/map/SiteMap'
import { LayerToggle } from '@/components/map/LayerToggle'
import { DrawTool } from '@/components/map/DrawTool'
import { BoundaryDisplay } from '@/components/map/BoundaryDisplay'
import { CoordinateInput } from '@/components/forms/CoordinateInput'
import { AddressSearch } from '@/components/forms/AddressSearch'
import { ResultsPanel } from '@/components/results/ResultsPanel'
import { ReportPanel } from '@/components/report/ReportPanel'
import { useBoundary } from '@/hooks/useBoundary'
import { useMapStore } from '@/store/mapStore'
import { MapPin, ChevronRight } from 'lucide-react'
import { MapContainer, TileLayer } from 'react-leaflet'

export default function HomeScreen() {
  const [showLayers, setShowLayers] = useState(false)
  const [rightTab, setRightTab] = useState<'results' | 'report'>('results')
  const { setSelectedCoords } = useMapStore()
  const center = useMapStore((s) => s.center)
  const zoom = useMapStore((s) => s.zoom)
  const selectedCoords = useMapStore((s) => s.selectedCoords)
  const setCenter = useMapStore((s) => s.setCenter)

  const boundary = useBoundary()

  const handleLocationSelect = (lat: number, lng: number) => {
    boundary.setCoords(lat, lng)
    setCenter([lat, lng])
    setSelectedCoords([lng, lat])
  }

  return (
    <div className="flex h-full">
      {/* Left panel */}
      <div className="w-72 flex flex-col border-r bg-white flex-shrink-0 overflow-y-auto">
        <div className="p-4 border-b bg-navy/5">
          <div className="flex items-center gap-2 mb-1">
            <MapPin className="w-4 h-4 text-navy" />
            <h1 className="text-sm font-bold text-slate">Site Search</h1>
          </div>
          <p className="text-xs text-gray-500">Click the map or enter coordinates</p>
        </div>

        <div className="p-4 space-y-5 flex-1">
          <AddressSearch onSelect={(lat, lng) => handleLocationSelect(lat, lng)} />

          <div className="border-t pt-4">
            <CoordinateInput onSubmit={handleLocationSelect} />
          </div>

          {boundary.coords && (
            <div className="border-t pt-4 space-y-2">
              <p className="text-xs font-semibold text-slate uppercase tracking-wide">Selected Site</p>
              <div className="bg-navy/5 rounded-md p-3 text-xs font-mono space-y-1">
                <div className="text-gray-600">Lat: {boundary.coords[1].toFixed(6)}</div>
                <div className="text-gray-600">Lon: {boundary.coords[0].toFixed(6)}</div>
              </div>
              <button
                onClick={boundary.clear}
                className="text-xs text-red-400 hover:text-red-600 transition-colors"
              >
                Clear selection
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Map */}
      <div className="flex-1 relative">
        <MapContainer
          center={center}
          zoom={zoom}
          className="w-full h-full"
          zoomControl
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          />
          <BoundaryDisplay bbox={boundary.bbox} />
        </MapContainer>

        {/* Map overlay controls */}
        <div className="absolute top-3 right-3 z-10 flex flex-col gap-2">
          <DrawTool />
          <button
            onClick={() => setShowLayers((s) => !s)}
            className="bg-white rounded-lg shadow-md p-2 hover:bg-gray-50 transition-colors"
            title="Toggle layers"
          >
            <ChevronRight className={`w-4 h-4 text-gray-600 transition-transform ${showLayers ? 'rotate-90' : ''}`} />
          </button>
          {showLayers && <LayerToggle />}
        </div>
      </div>

      {/* Right panel */}
      <div className="w-72 flex flex-col border-l bg-white flex-shrink-0">
        <div className="flex border-b">
          {(['results', 'report'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setRightTab(tab)}
              className={`flex-1 py-2 text-xs font-semibold uppercase tracking-wide transition-colors ${
                rightTab === tab
                  ? 'border-b-2 border-navy text-navy'
                  : 'text-gray-400 hover:text-gray-600'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
        <div className="flex-1 overflow-hidden">
          {rightTab === 'results' ? (
            <ResultsPanel results={[]} />
          ) : (
            <ReportPanel siteId="placeholder" />
          )}
        </div>
      </div>
    </div>
  )
}
