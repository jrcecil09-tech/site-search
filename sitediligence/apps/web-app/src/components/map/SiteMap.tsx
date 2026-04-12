import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet'
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
  const center = useMapStore((s) => s.center)
  const zoom   = useMapStore((s) => s.zoom)
  const selected = useMapStore((s) => s.selectedCoords)

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
