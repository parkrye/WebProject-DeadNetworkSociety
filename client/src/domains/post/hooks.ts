import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { postApi } from './api'

const POSTS_KEY = ['posts']

export function usePosts(page = 1) {
  return useQuery({
    queryKey: [...POSTS_KEY, page],
    queryFn: () => postApi.list(page),
  })
}

export function usePost(id: string) {
  return useQuery({
    queryKey: [...POSTS_KEY, id],
    queryFn: () => postApi.get(id),
    enabled: !!id,
  })
}

export function useCreatePost() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: postApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: POSTS_KEY })
    },
  })
}
