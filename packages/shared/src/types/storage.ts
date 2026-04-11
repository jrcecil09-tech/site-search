export type StorageBackend = 'local' | 's3' | 'azure' | 'gcs';

export type StorageClass = 'standard' | 'infrequent' | 'archive';

export interface StorageConfig {
  backend: StorageBackend;
  local?: LocalStorageConfig;
  s3?: S3StorageConfig;
  azure?: AzureStorageConfig;
  gcs?: GCSStorageConfig;
}

export interface LocalStorageConfig {
  rootPath: string;
  baseUrl: string;
}

export interface S3StorageConfig {
  bucket: string;
  region: string;
  accessKeyId?: string;     // Falls back to IAM role if omitted
  secretAccessKey?: string;
  endpoint?: string;        // For S3-compatible stores (MinIO, R2, etc.)
  forcePathStyle?: boolean;
  storageClass?: StorageClass;
}

export interface AzureStorageConfig {
  connectionString?: string;
  accountName?: string;
  accountKey?: string;
  containerName: string;
  sasToken?: string;
}

export interface GCSStorageConfig {
  bucket: string;
  keyFilename?: string;
  projectId?: string;
}

export interface StorageObject {
  key: string;
  bucket?: string;
  fileName: string;
  mimeType: string;
  size: number;
  url: string;
  signedUrl?: string;
  signedUrlExpiresAt?: string;
  uploadedAt: string;
  uploadedBy: string;
  metadata?: Record<string, string>;
}

export interface UploadRequest {
  fileName: string;
  mimeType: string;
  size: number;
  projectId: string;
  siteId?: string;
  observationId?: string;
}

export interface PresignedUpload {
  uploadUrl: string;
  fileKey: string;
  expiresAt: string;
  fields?: Record<string, string>;  // For S3 multipart POST
}
