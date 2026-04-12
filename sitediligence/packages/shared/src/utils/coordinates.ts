/**
 * Coordinate conversion and validation utilities.
 */

/** Decimal degrees coordinate pair [longitude, latitude] */
export type LonLat = [number, number];

/** Degrees, minutes, seconds representation */
export interface DMS {
  degrees: number;
  minutes: number;
  seconds: number;
  direction: 'N' | 'S' | 'E' | 'W';
}

/**
 * Convert decimal degrees to degrees/minutes/seconds.
 */
export function decimalToDMS(decimal: number, isLatitude: boolean): DMS {
  const abs = Math.abs(decimal);
  const degrees = Math.floor(abs);
  const minutesFloat = (abs - degrees) * 60;
  const minutes = Math.floor(minutesFloat);
  const seconds = (minutesFloat - minutes) * 60;

  let direction: DMS['direction'];
  if (isLatitude) {
    direction = decimal >= 0 ? 'N' : 'S';
  } else {
    direction = decimal >= 0 ? 'E' : 'W';
  }

  return { degrees, minutes, seconds: Math.round(seconds * 1000) / 1000, direction };
}

/**
 * Convert degrees/minutes/seconds to decimal degrees.
 */
export function dmsToDecimal(dms: DMS): number {
  const decimal = dms.degrees + dms.minutes / 60 + dms.seconds / 3600;
  return dms.direction === 'S' || dms.direction === 'W' ? -decimal : decimal;
}

/**
 * Format a coordinate pair as a human-readable string.
 * e.g. "38°53'23.5"N, 77°00'32.6"W"
 */
export function formatCoordinates(lonLat: LonLat): string {
  const [lon, lat] = lonLat;
  const latDMS = decimalToDMS(lat, true);
  const lonDMS = decimalToDMS(lon, false);
  const fmt = (d: DMS) =>
    `${d.degrees}°${d.minutes}'${d.seconds}"${d.direction}`;
  return `${fmt(latDMS)}, ${fmt(lonDMS)}`;
}

/**
 * Validate that a coordinate pair is within valid WGS84 bounds.
 */
export function isValidCoordinate(lonLat: LonLat): boolean {
  const [lon, lat] = lonLat;
  return lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180;
}

/**
 * Calculate the distance in meters between two WGS84 coordinate pairs
 * using the Haversine formula.
 */
export function haversineDistance(a: LonLat, b: LonLat): number {
  const R = 6371000; // Earth radius in meters
  const toRad = (deg: number) => (deg * Math.PI) / 180;

  const dLat = toRad(b[1] - a[1]);
  const dLon = toRad(b[0] - a[0]);
  const lat1 = toRad(a[1]);
  const lat2 = toRad(b[1]);

  const x =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;

  return R * 2 * Math.atan2(Math.sqrt(x), Math.sqrt(1 - x));
}
