import type { GeoJSONFeature, GeoJSONFeatureCollection, GeoJSONGeometry } from '../types/layers.js';
import type { GeoJSONBbox } from '../types/project.js';

/**
 * Create an empty GeoJSON FeatureCollection.
 */
export function emptyCollection(): GeoJSONFeatureCollection {
  return { type: 'FeatureCollection', features: [] };
}

/**
 * Wrap a geometry in a GeoJSON Feature.
 */
export function featureFromGeometry(
  geometry: GeoJSONGeometry,
  properties: Record<string, unknown> = {},
  id?: string | number,
): GeoJSONFeature {
  return { type: 'Feature', id, geometry, properties };
}

/**
 * Build a rectangular Polygon feature from a bounding box [minLng, minLat, maxLng, maxLat].
 */
export function featureFromBounds(bbox: GeoJSONBbox): GeoJSONFeature {
  const [minLng, minLat, maxLng, maxLat] = bbox;
  return featureFromGeometry({
    type: 'Polygon',
    coordinates: [[
      [minLng, minLat],
      [maxLng, minLat],
      [maxLng, maxLat],
      [minLng, maxLat],
      [minLng, minLat],
    ]],
  });
}

/**
 * Compute the bounding box of a FeatureCollection.
 * Returns null if the collection is empty.
 */
export function collectionBounds(collection: GeoJSONFeatureCollection): GeoJSONBbox | null {
  if (collection.features.length === 0) return null;
  let minLng = Infinity, minLat = Infinity, maxLng = -Infinity, maxLat = -Infinity;

  function processCoords(coords: unknown): void {
    if (typeof (coords as number[])[0] === 'number') {
      const [lng, lat] = coords as [number, number];
      if (lng < minLng) minLng = lng;
      if (lat < minLat) minLat = lat;
      if (lng > maxLng) maxLng = lng;
      if (lat > maxLat) maxLat = lat;
    } else {
      (coords as unknown[]).forEach(processCoords);
    }
  }

  for (const feature of collection.features) {
    if (feature.geometry) processCoords(feature.geometry.coordinates);
  }

  return [minLng, minLat, maxLng, maxLat];
}

/**
 * Return the centroid [lng, lat] of a bounding box.
 */
export function bboxCenter(bbox: GeoJSONBbox): [number, number] {
  return [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2];
}

/**
 * Test whether a point [lng, lat] falls inside a bounding box.
 */
export function pointInBbox(lng: number, lat: number, bbox: GeoJSONBbox): boolean {
  return lng >= bbox[0] && lng <= bbox[2] && lat >= bbox[1] && lat <= bbox[3];
}

/**
 * Expand a bounding box by a buffer in degrees on each side.
 */
export function bufferBbox(bbox: GeoJSONBbox, degrees: number): GeoJSONBbox {
  return [bbox[0] - degrees, bbox[1] - degrees, bbox[2] + degrees, bbox[3] + degrees];
}
