import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import { useProjectStore } from '@/store/projectStore'

export function PortfolioMap() {
  const projects = useProjectStore((s) => s.projects)

  return (
    <MapContainer
      center={[39.5, -98.35]}
      zoom={4}
      className="w-full h-full rounded-lg"
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      />
      {projects.map((p) => (
        <Marker key={p.id} position={[39.5, -98.35]}>
          <Popup>
            <div className="text-xs font-medium">{p.name}</div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}
