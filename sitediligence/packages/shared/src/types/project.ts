/**
 * Core project, site, and team interfaces.
 */

export type ProjectStatus = 'draft' | 'active' | 'completed' | 'archived';
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
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  tags: string[];
  sites: Site[];
}

export interface Site {
  id: string;
  projectId: string;
  name: string;
  description?: string;
  status: SiteStatus;
  address?: SiteAddress;
  /** GeoJSON point [longitude, latitude] */
  coordinates?: [number, number];
  /** Bounding box [minLon, minLat, maxLon, maxLat] */
  bbox?: [number, number, number, number];
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  metadata: Record<string, unknown>;
}

export interface SiteAddress {
  street?: string;
  city?: string;
  state?: string;
  zip?: string;
  country: string;
  county?: string;
  parcelId?: string;
}
