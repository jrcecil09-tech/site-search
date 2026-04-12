export type LayerType =
  | 'parcel'
  | 'zoning'
  | 'flood'
  | 'wetland'
  | 'soil'
  | 'aerial'
  | 'topographic'
  | 'utility'
  | 'cultural'
  | 'custom';

export type LayerFormat = 'geojson' | 'wms' | 'wmts' | 'xyz' | 'vector-tile' | 'shapefile' | 'kml' | 'dxf';

export type LayerVisibility = 'visible' | 'hidden';

export interface LayerStyle {
  color?: string;
  fillColor?: string;
  fillOpacity?: number;
  strokeWidth?: number;
  strokeOpacity?: number;
  iconUrl?: string;
  labelField?: string;
}

export interface GISLayer {
  id: string;
  projectId: string;
  name: string;
  type: LayerType;
  format: LayerFormat;
  url?: string;
  fileKey?: string;       // Storage key for uploaded file
  visibility: LayerVisibility;
  opacity: number;        // 0–1
  zIndex: number;
  style: LayerStyle;
  attribution?: string;
  agency?: string;
  lastFetched?: string;
  createdAt: string;
  updatedAt: string;
}

export interface LayerFeatureProperties {
  [key: string]: string | number | boolean | null;
}

export interface GeoJSONFeature {
  type: 'Feature';
  id?: string | number;
  geometry: GeoJSONGeometry;
  properties: LayerFeatureProperties;
}

export interface GeoJSONFeatureCollection {
  type: 'FeatureCollection';
  features: GeoJSONFeature[];
  bbox?: [number, number, number, number];
}

export type GeoJSONGeometry =
  | { type: 'Point'; coordinates: [number, number] }
  | { type: 'LineString'; coordinates: [number, number][] }
  | { type: 'Polygon'; coordinates: [number, number][][] }
  | { type: 'MultiPoint'; coordinates: [number, number][] }
  | { type: 'MultiLineString'; coordinates: [number, number][][] }
  | { type: 'MultiPolygon'; coordinates: [number, number][][][] };
