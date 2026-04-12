import { MapContainer, TileLayer, WMSTileLayer, Marker, Popup, useMapEvents } from 'react-leaflet'
import { useMapStore } from '@/store/mapStore'
import { cn } from '@/lib/utils'

interface LocationPickerProps {
  onSelect: (lat: number, lng: number) => void
}

function LocationPicker({ onSelect }: LocationPickerProps) {
  useMapEvents({ click: (e) => onSelect(e.latlng.lat, e.latlng.lng) })
  return null
}

interface SiteMapProps {
  className?: string
  onLocationSelect?: (lat: number, lng: number) => void
}

export function SiteMap({ className, onLocationSelect }: SiteMapProps) {
  const center   = useMapStore((s) => s.center)
  const zoom     = useMapStore((s) => s.zoom)
  const selected = useMapStore((s) => s.selectedCoords)
  const layers   = useMapStore((s) => s.layers)

  const wetlandsLayer = layers.find((l) => l.id === 'wetlands')
  const floodLayer    = layers.find((l) => l.id === 'flood')

  return (
    <MapContainer
      center={center}
      zoom={zoom}
      className={cn('w-full h-full', className)}
      zoomControl
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        maxZoom={19}
      />

      {wetlandsLayer?.visible && (
        <WMSTileLayer
          url="https://www.fws.gov/wetlandsmapservice/services/Wetlands/MapServer/WMSServer"
          layers="0"
          format="image/png"
          transparent
          opacity={wetlandsLayer.opacity}
          attribution='<a href="https://www.fws.gov/program/national-wetlands-inventory">USFWS NWI</a>'
          version="1.3.0"
        />
      )}

      {floodLayer?.visible && (
        <WMSTileLayer
          url="https://hazards.fema.gov/arcgis/services/public/NFHL/MapServer/WMSServer"
          layers="28"
          format="image/png"
          transparent
          opacity={floodLayer.opacity}
          attribution='<a href="https://www.fema.gov/flood-maps">FEMA NFHL</a>'
          version="1.3.0"
        />
      )}

      {onLocationSelect && <LocationPicker onSelect={onLocationSelect} />}

      {selected && (
        <Marker position={[selected[1], selected[0]]}>
          <Popup>
            <div className="text-xs font-mono">
              <div>{selected[1].toFixed(6)}°N</div>
              <div>{selected[0].toFixed(6)}°W</div>
            </div>
          </Popup>
        </Marker>
      )}
    </MapContainer>
  )
}
