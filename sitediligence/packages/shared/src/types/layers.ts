/**
 * GIS layer data interfaces.
 */

export type LayerType = 'vector' | 'raster' | 'wms' | 'wmts' | 'xyz' | 'geojson';
export type GeometryType = 'Point' | 'LineString' | 'Polygon' | 'MultiPoint' | 'MultiLineString' | 'MultiPolygon';

export interface LayerSource {
  type: LayerType;
  url?: string;
  data?: GeoJSONFeatureCollection;
  attribution?: string;
  /** WMS/WMTS layer name */
  layers?: string;
  format?: string;
  tileSize?: number;
  minZoom?: number;
  maxZoom?: number;
}

export interface LayerStyle {
  color?: string;
  fillColor?: string;
  fillOpacity?: number;
  opacity?: number;
  weight?: number;
  dashArray?: string;
  radius?: number;
}

export interface MapLayer {
  id: string;
  name: string;
  category: string;
  description?: string;
  source: LayerSource;
  style?: LayerStyle;
  visible: boolean;
  opacity: number;
  zIndex?: number;
  metadata?: Record<string, unknown>;
}

export interface SiteLayer extends MapLayer {
  siteId: string;
  uploadedAt: string;
  uploadedBy: string;
  fileSize?: number;
  fileName?: string;
}

// Minimal GeoJSON types (avoid pulling in a full GeoJSON lib)
export interface GeoJSONPoint {
  type: 'Point';
  coordinates: [number, number] | [number, number, number];
}

export interface GeoJSONFeature {
  type: 'Feature';
  geometry: { type: GeometryType; coordinates: unknown };
  properties: Record<string, unknown> | null;
  id?: string | number;
}

export interface GeoJSONFeatureCollection {
  type: 'FeatureCollection';
  features: GeoJSONFeature[];
}
