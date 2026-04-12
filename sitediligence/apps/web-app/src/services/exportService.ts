import { api } from './api'

export interface ExportRequest {
  site_id: string
  format: string
  include_attachments?: boolean
  include_layers?: boolean
  include_observations?: boolean
  crs?: number
  page_size?: string
  orientation?: string
}

export const exportService = {
  getFormats: () =>
    api.get<{ formats: string[] }>('/api/v1/exports/formats'),

  create: (req: ExportRequest) =>
    api.post<{ job_id: string }>('/api/v1/exports', req),

  getStatus: (jobId: string) =>
    api.get<{ status: string; download_url?: string }>(`/api/v1/exports/${jobId}/status`),

  download: (jobId: string) =>
    api.get(`/api/v1/exports/${jobId}/download`, { responseType: 'blob' }),
}
