import { Rectangle } from 'react-leaflet'

interface BoundaryDisplayProps {
  bbox: [number, number, number, number] | null // [minLon, minLat, maxLon, maxLat]
}

export function BoundaryDisplay({ bbox }: BoundaryDisplayProps) {
  if (!bbox) return null
  const [minLon, minLat, maxLon, maxLat] = bbox
  const bounds: [[number, number], [number, number]] = [
    [minLat, minLon],
    [maxLat, maxLon],
  ]
  return (
    <Rectangle
      bounds={bounds}
      pathOptions={{ color: '#1B4F72', weight: 2, fillOpacity: 0.05, dashArray: '6 4' }}
    />
  )
}
