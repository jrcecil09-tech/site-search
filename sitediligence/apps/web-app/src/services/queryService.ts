import { api } from './api'

export interface QueryRequest {
  site_id: string
  query_types: string[]
  bbox?: [number, number, number, number]
  buffer_meters?: number
}

export interface QueryJob {
  job_id: string
  status: 'queued' | 'processing' | 'complete' | 'error'
  results?: Record<string, unknown>
}

export const queryService = {
  getAvailable: () => api.get<{ queries: string[] }>('/api/v1/queries/available'),

  run: (req: QueryRequest) =>
    api.post<{ job_id: string }>('/api/v1/queries/run', req),

  getResults: (jobId: string) =>
    api.get<QueryJob>(`/api/v1/queries/results/${jobId}`),
}
