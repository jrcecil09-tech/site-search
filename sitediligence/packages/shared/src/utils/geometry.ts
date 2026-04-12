/**
 * GeoJSON helper utilities.
 */

import type { GeoJSONFeature, GeoJSONFeatureCollection, GeoJSONPoint } from '../types/layers.js';
import type { LonLat } from './coordinates.js';

/**
 * Create a GeoJSON Feature from a coordinate pair and properties.
 */
export function makePointFeature(
  lonLat: LonLat,
  properties: Record<string, unknown> = {}
): GeoJSONFeature {
  return {
    type: 'Feature',
    geometry: {
      type: 'Point',
      coordinates: lonLat,
    } satisfies GeoJSONPoint,
    properties,
  };
}

/**
 * Wrap an array of features into a FeatureCollection.
 */
export function makeFeatureCollection(
  features: GeoJSONFeature[]
): GeoJSONFeatureCollection {
  return { type: 'FeatureCollection', features };
}

/**
 * Compute the bounding box of a FeatureCollection.
 * Returns [minLon, minLat, maxLon, maxLat] or null if no point features.
 */
export function getBbox(
  collection: GeoJSONFeatureCollection
): [number, number, number, number] | null {
  let minLon = Infinity;
  let minLat = Infinity;
  let maxLon = -Infinity;
  let maxLat = -Infinity;

  for (const feature of collection.features) {
    const coords = extractCoordinates(feature.geometry.coordinates);
    for (const [lon, lat] of coords) {
      if (lon < minLon) minLon = lon;
      if (lat < minLat) minLat = lat;
      if (lon > maxLon) maxLon = lon;
      if (lat > maxLat) maxLat = lat;
    }
  }

  if (!isFinite(minLon)) return null;
  return [minLon, minLat, maxLon, maxLat];
}

/**
 * Recursively flatten nested coordinate arrays into [lon, lat] pairs.
 */
function extractCoordinates(coords: unknown): LonLat[] {
  if (!Array.isArray(coords)) return [];
  if (typeof coords[0] === 'number') {
    return [[coords[0] as number, coords[1] as number]];
  }
  return (coords as unknown[]).flatMap((c) => extractCoordinates(c));
}

/**
 * Return true if a point [lon, lat] is inside a bounding box.
 */
export function pointInBbox(
  point: LonLat,
  bbox: [number, number, number, number]
): boolean {
  const [lon, lat] = point;
  const [minLon, minLat, maxLon, maxLat] = bbox;
  return lon >= minLon && lon <= maxLon && lat >= minLat && lat <= maxLat;
}
