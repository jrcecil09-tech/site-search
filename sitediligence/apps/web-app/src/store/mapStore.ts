import { create } from 'zustand'

export interface MapLayer {
  id: string
  name: string
  visible: boolean
  opacity: number
  category: string
}

interface MapState {
  center: [number, number]
  zoom: number
  activeLayers: string[]
  selectedCoords: [number, number] | null
  layers: MapLayer[]
  setCenter: (center: [number, number]) => void
  setZoom: (zoom: number) => void
  setSelectedCoords: (coords: [number, number] | null) => void
  toggleLayer: (layerId: string) => void
  setLayerOpacity: (layerId: string, opacity: number) => void
}

const DEFAULT_LAYERS: MapLayer[] = [
  { id: 'osm',       name: 'OpenStreetMap',    visible: true,  opacity: 1,   category: 'base' },
  { id: 'satellite', name: 'Satellite',         visible: false, opacity: 1,   category: 'base' },
  { id: 'wetlands',  name: 'NWI Wetlands',      visible: false, opacity: 0.7, category: 'environmental' },
  { id: 'flood',     name: 'FEMA Flood Zones',  visible: false, opacity: 0.6, category: 'regulatory' },
  { id: 'streams',   name: 'NHD Streams',        visible: false, opacity: 0.8, category: 'hydrography' },
  { id: 'soils',     name: 'SSURGO Soils',        visible: false, opacity: 0.55, category: 'soils' },
]

export const useMapStore = create<MapState>()((set) => ({
  center: [39.5, -98.35], // Continental US
  zoom: 4,
  activeLayers: ['osm'],
  selectedCoords: null,
  layers: DEFAULT_LAYERS,

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
}))
