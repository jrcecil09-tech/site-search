import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { exportService, type ExportRequest } from '@/services/exportService'
import toast from 'react-hot-toast'

export function useExportFormats() {
  return useQuery({
    queryKey: ['export-formats'],
    queryFn: () => exportService.getFormats().then((r) => r.data.formats),
  })
}

export function useExport() {
  const [jobId, setJobId] = useState<string | null>(null)

  const create = useMutation({
    mutationFn: (req: ExportRequest) =>
      exportService.create(req).then((r) => r.data),
    onSuccess: (data) => {
      setJobId(data.job_id)
      toast.success('Export queued — preparing your file…')
    },
    onError: () => toast.error('Export failed. Please try again.'),
  })

  const status = useQuery({
    queryKey: ['export-status', jobId],
    queryFn: () => exportService.getStatus(jobId!).then((r) => r.data),
    enabled: !!jobId,
    refetchInterval: (q) => {
      const s = q.state.data?.status
      return s === 'queued' || s === 'processing' ? 2000 : false
    },
  })

  return { create, status, jobId, clearJob: () => setJobId(null) }
}
