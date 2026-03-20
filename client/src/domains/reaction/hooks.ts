import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { reactionApi } from './api'

export function useReactionCounts(targetType: string, targetId: string) {
  return useQuery({
    queryKey: ['reactions', targetType, targetId],
    queryFn: () => reactionApi.getCounts(targetType, targetId),
    enabled: !!targetId,
  })
}

export function useToggleReaction() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: reactionApi.toggle,
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['reactions', variables.target_type, variables.target_id],
      })
    },
  })
}
