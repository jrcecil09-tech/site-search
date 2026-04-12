/**
 * Field observation interfaces.
 */

export type ObservationStatus = 'draft' | 'submitted' | 'reviewed' | 'flagged';
export type AttachmentType = 'photo' | 'video' | 'audio' | 'document' | 'sketch';
export type SeverityLevel = 'info' | 'low' | 'medium' | 'high' | 'critical';

export interface Observation {
  id: string;
  siteId: string;
  projectId: string;
  categoryId: string;
  title: string;
  description?: string;
  status: ObservationStatus;
  severity: SeverityLevel;
  /** GeoJSON point [longitude, latitude] where observation was made */
  coordinates?: [number, number];
  attachments: ObservationAttachment[];
  tags: string[];
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  reviewedBy?: string;
  reviewedAt?: string;
  reviewNotes?: string;
  customFields: Record<string, unknown>;
}

export interface ObservationAttachment {
  id: string;
  observationId: string;
  type: AttachmentType;
  fileName: string;
  fileSize: number;
  contentType: string;
  storageKey: string;
  url?: string;
  /** EXIF or video metadata */
  capturedAt?: string;
  captureLocation?: [number, number];
  uploadedAt: string;
  uploadedBy: string;
}

export interface ObservationCategory {
  id: string;
  name: string;
  description?: string;
  color: string;
  icon?: string;
  parentId?: string;
  sortOrder: number;
}

export interface ObservationFilter {
  siteId?: string;
  projectId?: string;
  categoryIds?: string[];
  status?: ObservationStatus[];
  severity?: SeverityLevel[];
  createdBy?: string;
  dateFrom?: string;
  dateTo?: string;
  tags?: string[];
}
