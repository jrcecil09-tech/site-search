/**
 * Layer names, colors, and categories for map display.
 */

export const LAYER_CATEGORIES = {
  REGULATORY: 'regulatory',
  ENVIRONMENTAL: 'environmental',
  INFRASTRUCTURE: 'infrastructure',
  PARCEL: 'parcel',
  TOPOGRAPHY: 'topography',
  IMAGERY: 'imagery',
  CUSTOM: 'custom',
} as const;

export type LayerCategory = (typeof LAYER_CATEGORIES)[keyof typeof LAYER_CATEGORIES];

export const LAYER_COLORS: Record<LayerCategory, string> = {
  regulatory: '#e74c3c',
  environmental: '#27ae60',
  infrastructure: '#3498db',
  parcel: '#f39c12',
  topography: '#8e44ad',
  imagery: '#95a5a6',
  custom: '#2c3e50',
};

export const BASE_LAYERS = {
  OSM: {
    id: 'osm',
    name: 'OpenStreetMap',
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '© OpenStreetMap contributors',
  },
  SATELLITE: {
    id: 'satellite',
    name: 'Satellite',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Tiles © Esri',
  },
  TOPO: {
    id: 'topo',
    name: 'USGS Topo',
    url: 'https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}',
    attribution: 'USGS The National Map',
  },
} as const;

export const FEDERAL_LAYER_SOURCES = {
  WETLANDS: {
    id: 'nwi-wetlands',
    name: 'NWI Wetlands',
    category: LAYER_CATEGORIES.ENVIRONMENTAL,
    wmsUrl: 'https://www.fws.gov/wetlands/arcgis/services/Wetlands/MapServer/WMSServer',
    layers: 'Wetlands',
  },
  FLOOD_ZONES: {
    id: 'fema-flood',
    name: 'FEMA Flood Zones',
    category: LAYER_CATEGORIES.REGULATORY,
    wmsUrl: 'https://hazards.fema.gov/gis/nfhl/services/public/NFHLWMS/MapServer/WmsServer',
    layers: 'FIRM_Panel,Flood_Hazard_Zone',
  },
  PROTECTED_AREAS: {
    id: 'pad-us',
    name: 'Protected Areas (PAD-US)',
    category: LAYER_CATEGORIES.REGULATORY,
    wmsUrl: 'https://gis1.usgs.gov/arcgis/services/PADUS3/PADUS3_0Combined/MapServer/WmsServer',
    layers: '0',
  },
} as const;
