import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { userApi } from './api'

export function useUserStats(userId: string) {
  return useQuery({
    queryKey: ['user-stats', userId],
    queryFn: () => userApi.stats(userId),
    enabled: !!userId,
  })
}

export function useRanking() {
  return useQuery({
    queryKey: ['ranking'],
    queryFn: () => userApi.ranking(),
    refetchInterval: 30000,
  })
}

export function useUpdateUser(userId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { nickname?: string; bio?: string; avatar_url?: string }) =>
      userApi.update(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-stats', userId] })
    },
  })
}
