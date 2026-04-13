import { create } from 'zustand'

export interface MapLayer {
  id: string
  name: string
  visible: boolean
  opacity: number
  category: string
}

export interface EpaMarker {
  lat: number
  lon: number
  name: string
  category: 'superfund' | 'rcra' | 'tri' | 'frs' | 'echo'
  color: string
  detail?: string
}

interface MapState {
  center: [number, number]
  zoom: number
  activeLayers: string[]
  selectedCoords: [number, number] | null
  layers: MapLayer[]
  epaMarkers: EpaMarker[]
  setCenter: (center: [number, number]) => void
  setZoom: (zoom: number) => void
  setSelectedCoords: (coords: [number, number] | null) => void
  toggleLayer: (layerId: string) => void
  setLayerOpacity: (layerId: string, opacity: number) => void
  setEpaMarkers: (markers: EpaMarker[]) => void
  clearEpaMarkers: () => void
}

const DEFAULT_LAYERS: MapLayer[] = [
  { id: 'osm',       name: 'OpenStreetMap',    visible: true,  opacity: 1,   category: 'base' },
  { id: 'satellite', name: 'Satellite',         visible: false, opacity: 1,   category: 'base' },
  { id: 'wetlands',  name: 'NWI Wetlands',      visible: false, opacity: 0.7, category: 'environmental' },
  { id: 'flood',     name: 'FEMA Flood Zones',  visible: false, opacity: 0.6, category: 'regulatory' },
  { id: 'streams',   name: 'NHD Streams',        visible: false, opacity: 0.8, category: 'hydrography' },
  { id: 'soils',     name: 'SSURGO Soils',        visible: false, opacity: 0.55, category: 'soils' },
  { id: 'epa',       name: 'EPA Facilities',       visible: false, opacity: 1,    category: 'regulatory' },
]

export const useMapStore = create<MapState>()((set) => ({
  center: [39.5, -98.35], // Continental US
  zoom: 4,
  activeLayers: ['osm'],
  selectedCoords: null,
  layers: DEFAULT_LAYERS,
  epaMarkers: [],

  setCenter: (center) => set({ center }),
  setZoom: (zoom) => set({ zoom }),
  setSelectedCoords: (coords) => set({ selectedCoords: coords }),

  toggleLayer: (layerId) =>
    set((s) => ({
      activeLayers: s.activeLayers.includes(layerId)
        ? s.activeLayers.filter((id) => id !== layerId)
        : [...s.activeLayers, layerId],
      layers: s.layers.map((l) =>
        l.id === layerId ? { ...l, visible: !l.visible } : l,
      ),
    })),

  setLayerOpacity: (layerId, opacity) =>
    set((s) => ({
      layers: s.layers.map((l) => (l.id === layerId ? { ...l, opacity } : l)),
    })),

  setEpaMarkers: (markers) => set({ epaMarkers: markers }),
  clearEpaMarkers: () => set({ epaMarkers: [] }),
}))
