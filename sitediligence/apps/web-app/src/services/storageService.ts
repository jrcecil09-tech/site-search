import { api } from './api'

export const storageService = {
  listFiles: (siteId: string) =>
    api.get<{ files: Array<{ key: string; size: number; content_type: string }> }>(
      `/api/v1/storage/files/${siteId}`,
    ),

  upload: (siteId: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/api/v1/storage/upload?site_id=${siteId}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  deleteFile: (siteId: string, fileKey: string) =>
    api.delete(`/api/v1/storage/files/${siteId}/${fileKey}`),

  getConfig: () => api.get('/api/v1/storage/config'),

  updateConfig: (config: { backend: string; config: Record<string, unknown> }) =>
    api.put('/api/v1/storage/config', config),
}
