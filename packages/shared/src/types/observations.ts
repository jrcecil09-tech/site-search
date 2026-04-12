export type ObservationSeverity = 'info' | 'low' | 'moderate' | 'high' | 'critical';
export type ObservationStatus = 'draft' | 'submitted' | 'reviewed' | 'resolved' | 'dismissed';

export interface Observation {
  id: string;
  siteId: string;
  projectId: string;
  category: string;
  subcategory?: string;
  title: string;
  description: string;
  severity: ObservationSeverity;
  status: ObservationStatus;
  location?: ObservationLocation;
  attachments: Attachment[];
  tags: string[];
  regulatoryRefs: RegulatoryReference[];
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  reviewedBy?: string;
  reviewedAt?: string;
  reviewNotes?: string;
}

export interface ObservationLocation {
  latitude: number;
  longitude: number;
  altitude?: number;
  accuracy?: number;          // meters
  heading?: number;           // degrees
  capturedAt?: string;
  address?: string;
}

export interface Attachment {
  id: string;
  observationId: string;
  fileName: string;
  mimeType: string;
  size: number;
  url: string;
  thumbnailUrl?: string;
  caption?: string;
  takenAt?: string;
  location?: ObservationLocation;
  uploadedAt: string;
  uploadedBy: string;
}

export interface RegulatoryReference {
  agency: string;
  programName: string;
  cfrCitation?: string;        // e.g. "40 CFR Part 261"
  url?: string;
  notes?: string;
}

export interface ObservationFilter {
  categories?: string[];
  severities?: ObservationSeverity[];
  statuses?: ObservationStatus[];
  tags?: string[];
  createdAfter?: string;
  createdBefore?: string;
  createdBy?: string;
  search?: string;
}
