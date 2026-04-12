/**
 * Export format interfaces.
 */

export type ExportFormat = 'pdf' | 'docx' | 'xlsx' | 'csv' | 'geojson' | 'kml' | 'shapefile' | 'dxf';
export type ExportStatus = 'queued' | 'processing' | 'ready' | 'failed' | 'expired';

export interface ExportOptions {
  format: ExportFormat;
  includeAttachments: boolean;
  includeLayers: boolean;
  includeObservations: boolean;
  includeMetadata: boolean;
  /** Coordinate reference system EPSG code, e.g. 4326 */
  crs?: number;
  /** Page size for PDF/DOCX exports */
  pageSize?: 'letter' | 'legal' | 'a4';
  orientation?: 'portrait' | 'landscape';
}

export interface ExportJob {
  id: string;
  siteId: string;
  projectId: string;
  requestedBy: string;
  requestedAt: string;
  options: ExportOptions;
  status: ExportStatus;
  downloadUrl?: string;
  expiresAt?: string;
  errorMessage?: string;
  fileSizeBytes?: number;
}

export interface ExportTemplate {
  id: string;
  name: string;
  description?: string;
  format: ExportFormat;
  options: Partial<ExportOptions>;
  isDefault: boolean;
}
