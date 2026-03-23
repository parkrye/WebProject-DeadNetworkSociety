import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { followApi } from './api'

export function useFollowStatus(userId: string, viewerId: string | null) {
  return useQuery({
    queryKey: ['follow-status', userId, viewerId],
    queryFn: () => followApi.check(userId, viewerId!),
    enabled: !!viewerId && viewerId !== userId,
  })
}

export function useToggleFollow(userId: string, viewerId: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => followApi.toggle(viewerId!, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['follow-status', userId, viewerId] })
      queryClient.invalidateQueries({ queryKey: ['user-stats', userId] })
    },
  })
}
