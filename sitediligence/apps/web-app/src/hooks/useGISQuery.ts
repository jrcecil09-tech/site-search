import { useMutation, useQuery } from '@tanstack/react-query'
import { queryService, type QueryRequest } from '@/services/queryService'

export function useAvailableQueries() {
  return useQuery({
    queryKey: ['queries', 'available'],
    queryFn: () => queryService.getAvailable().then((r) => r.data.queries),
  })
}

export function useRunQuery() {
  return useMutation({
    mutationFn: (req: QueryRequest) =>
      queryService.run(req).then((r) => r.data),
  })
}

export function useQueryResults(jobId: string | null) {
  return useQuery({
    queryKey: ['query-results', jobId],
    queryFn: () => queryService.getResults(jobId!).then((r) => r.data),
    enabled: !!jobId,
    refetchInterval: (q) => {
      const status = q.state.data?.status
      return status === 'queued' || status === 'processing' ? 2000 : false
    },
  })
}
