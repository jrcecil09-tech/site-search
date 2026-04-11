export type ExportFormat = 'pdf' | 'docx' | 'xlsx' | 'geojson' | 'shapefile' | 'kml' | 'dxf' | 'csv';

export type ExportStatus = 'queued' | 'processing' | 'complete' | 'failed';

export type ReportTemplate =
  | 'site-summary'
  | 'full-diligence'
  | 'observation-log'
  | 'layer-inventory'
  | 'custom';

export interface ExportOptions {
  format: ExportFormat;
  template?: ReportTemplate;
  includeAttachments: boolean;
  includeLayers: boolean;
  includeObservations: boolean;
  includeMap: boolean;
  mapZoom?: number;
  pageSize?: 'letter' | 'legal' | 'a4';
  orientation?: 'portrait' | 'landscape';
}

export interface ExportJob {
  id: string;
  projectId: string;
  siteId?: string;
  status: ExportStatus;
  format: ExportFormat;
  options: ExportOptions;
  fileKey?: string;       // Storage key once complete
  downloadUrl?: string;
  fileSize?: number;
  error?: string;
  requestedBy: string;
  createdAt: string;
  completedAt?: string;
}

export interface ExportRecord {
  id: string;
  projectId: string;
  jobId: string;
  fileName: string;
  format: ExportFormat;
  fileSize: number;
  downloadUrl: string;
  expiresAt: string;
  createdAt: string;
}
