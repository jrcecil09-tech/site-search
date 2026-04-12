/**
 * Storage configuration interfaces.
 */

export type StorageBackend = 'local' | 's3' | 'azure' | 'gcs' | 'hosted';

export interface StorageConfig {
  backend: StorageBackend;
  local?: LocalStorageConfig;
  s3?: S3StorageConfig;
  azure?: AzureStorageConfig;
  gcs?: GCSStorageConfig;
  hosted?: HostedStorageConfig;
}

export interface LocalStorageConfig {
  basePath: string;
}

export interface S3StorageConfig {
  bucket: string;
  region: string;
  accessKeyId: string;
  secretAccessKey: string;
  /** Optional custom endpoint (Cloudflare R2, MinIO, etc.) */
  endpointUrl?: string;
  prefix?: string;
  publicUrlBase?: string;
}

export interface AzureStorageConfig {
  connectionString: string;
  containerName: string;
  prefix?: string;
}

export interface GCSStorageConfig {
  bucket: string;
  credentialsFile?: string;
  prefix?: string;
}

export interface HostedStorageConfig {
  apiUrl: string;
  apiKey: string;
  organizationId: string;
}

export interface StorageObject {
  key: string;
  bucket?: string;
  contentType: string;
  sizeBytes: number;
  uploadedAt: string;
  uploadedBy: string;
  url?: string;
  metadata?: Record<string, string>;
}
