const EARTH_RADIUS_METERS = 6_378_137;
const DEG_TO_RAD = Math.PI / 180;
const RAD_TO_DEG = 180 / Math.PI;

/**
 * Convert degrees to radians.
 */
export function toRadians(degrees: number): number {
  return degrees * DEG_TO_RAD;
}

/**
 * Convert radians to degrees.
 */
export function toDegrees(radians: number): number {
  return radians * RAD_TO_DEG;
}

/**
 * Convert WGS84 [longitude, latitude] to Web Mercator [x, y] in meters.
 */
export function toWebMercator(lng: number, lat: number): [x: number, y: number] {
  const x = lng * DEG_TO_RAD * EARTH_RADIUS_METERS;
  const y = Math.log(Math.tan(Math.PI / 4 + (lat * DEG_TO_RAD) / 2)) * EARTH_RADIUS_METERS;
  return [x, y];
}

/**
 * Convert Web Mercator [x, y] in meters back to WGS84 [longitude, latitude].
 */
export function fromWebMercator(x: number, y: number): [lng: number, lat: number] {
  const lng = (x / EARTH_RADIUS_METERS) * RAD_TO_DEG;
  const lat = (2 * Math.atan(Math.exp(y / EARTH_RADIUS_METERS)) - Math.PI / 2) * RAD_TO_DEG;
  return [lng, lat];
}

/**
 * Haversine distance between two WGS84 points, in meters.
 */
export function haversineDistance(
  lng1: number, lat1: number,
  lng2: number, lat2: number,
): number {
  const dLat = toRadians(lat2 - lat1);
  const dLng = toRadians(lng2 - lng1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) * Math.sin(dLng / 2) ** 2;
  return 2 * EARTH_RADIUS_METERS * Math.asin(Math.sqrt(a));
}

/**
 * Parse a DMS string like "38°53'23.1\"N" → decimal degrees.
 */
export function dmsToDecimal(dms: string): number {
  const match = dms.match(/(\d+)[°\s](\d+)['\'\s]([0-9.]+)["\s]*([NSEW])?/i);
  if (!match) throw new Error(`Cannot parse DMS string: "${dms}"`);
  const [, d, m, s, dir] = match;
  let decimal = Number(d) + Number(m) / 60 + Number(s) / 3600;
  if (dir && /[SW]/i.test(dir)) decimal = -decimal;
  return decimal;
}

/**
 * Format decimal degrees as DMS string.
 */
export function decimalToDMS(decimal: number, isLat: boolean): string {
  const abs = Math.abs(decimal);
  const deg = Math.floor(abs);
  const minFull = (abs - deg) * 60;
  const min = Math.floor(minFull);
  const sec = ((minFull - min) * 60).toFixed(2);
  const dir = isLat ? (decimal >= 0 ? 'N' : 'S') : decimal >= 0 ? 'E' : 'W';
  return `${deg}°${min}'${sec}"${dir}`;
}

/**
 * Clamp a longitude to [-180, 180].
 */
export function normalizeLng(lng: number): number {
  return ((((lng + 180) % 360) + 360) % 360) - 180;
}

/**
 * Clamp a latitude to [-90, 90].
 */
export function normalizeLat(lat: number): number {
  return Math.max(-90, Math.min(90, lat));
}
