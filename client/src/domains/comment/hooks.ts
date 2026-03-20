import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { commentApi } from './api'

export function useCommentsByPost(postId: string) {
  return useQuery({
    queryKey: ['comments', postId],
    queryFn: () => commentApi.listByPost(postId),
    enabled: !!postId,
  })
}

export function useCreateComment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: commentApi.create,
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['comments', variables.post_id] })
    },
  })
}
