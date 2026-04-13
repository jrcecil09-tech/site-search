import { MapContainer, TileLayer, WMSTileLayer, Marker, Popup, CircleMarker, useMapEvents } from 'react-leaflet'
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
  const streamsLayer  = layers.find((l) => l.id === 'streams')
  const soilsLayer    = layers.find((l) => l.id === 'soils')
  const epaLayer      = layers.find((l) => l.id === 'epa')
  const epaMarkers    = useMapStore((s) => s.epaMarkers)

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

      {streamsLayer?.visible && (
        <WMSTileLayer
          url="https://hydro.nationalmap.gov/arcgis/services/NHDPlus_HR/MapServer/WMSServer"
          layers="2,10"
          format="image/png"
          transparent
          opacity={streamsLayer.opacity}
          attribution='<a href="https://www.usgs.gov/national-hydrography">USGS NHD</a>'
          version="1.3.0"
        />
      )}

      {soilsLayer?.visible && (
        <WMSTileLayer
          url="https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDM.wms"
          layers="mapunitpoly"
          format="image/png"
          transparent
          opacity={soilsLayer.opacity}
          attribution='<a href="https://www.nrcs.usda.gov/resources/data-and-reports/web-soil-survey">USDA NRCS WSS</a>'
          version="1.1.1"
        />
      )}

      {epaLayer?.visible && epaMarkers.map((m, i) => (
        <CircleMarker
          key={i}
          center={[m.lat, m.lon]}
          radius={m.category === 'superfund' ? 10 : 7}
          pathOptions={{
            color: m.color,
            fillColor: m.color,
            fillOpacity: 0.85,
            weight: m.category === 'superfund' ? 2 : 1.5,
          }}
        >
          <Popup>
            <div className="text-xs space-y-0.5">
              <div className="font-semibold">{m.name}</div>
              <div className="uppercase text-gray-500 tracking-wide text-[10px]">
                {m.category === 'superfund' ? 'Superfund / CERCLA' :
                 m.category === 'rcra'      ? 'RCRA Hazardous Waste' :
                 m.category === 'tri'       ? 'TRI Toxic Release' : 'EPA Facility'}
              </div>
              {m.detail && <div className="text-gray-600">{m.detail}</div>}
            </div>
          </Popup>
        </CircleMarker>
      ))}

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
