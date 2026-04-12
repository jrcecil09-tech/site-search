export type ProjectStatus = 'active' | 'archived' | 'draft' | 'complete';
export type SiteStatus = 'pending' | 'in-progress' | 'reviewed' | 'approved';
export type TeamRole = 'owner' | 'admin' | 'editor' | 'viewer';

export interface Team {
  id: string;
  name: string;
  slug: string;
  createdAt: string;
  members: TeamMember[];
}

export interface TeamMember {
  userId: string;
  email: string;
  displayName: string;
  role: TeamRole;
  joinedAt: string;
}

export interface Project {
  id: string;
  teamId: string;
  name: string;
  description?: string;
  status: ProjectStatus;
  bounds?: GeoJSONBbox;        // [minLng, minLat, maxLng, maxLat]
  coverImageUrl?: string;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  siteCount: number;
  tags: string[];
}

export interface Site {
  id: string;
  projectId: string;
  name: string;
  address?: string;
  status: SiteStatus;
  location?: GeoJSONPoint;
  bounds?: GeoJSONBbox;
  parcelId?: string;
  acreage?: number;
  notes?: string;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  observationCount: number;
  tags: string[];
}

export interface GeoJSONPoint {
  type: 'Point';
  coordinates: [longitude: number, latitude: number];
}

export type GeoJSONBbox = [minLng: number, minLat: number, maxLng: number, maxLat: number];
