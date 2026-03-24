import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { postApi } from './api'

const POSTS_KEY = ['posts']
const FEED_KEY = ['feed']
const POPULAR_KEY = ['popular-feed']

export function useFeed(page = 1) {
  return useQuery({
    queryKey: [...FEED_KEY, page],
    queryFn: () => postApi.feed(page),
    refetchInterval: 15000,
  })
}

export function usePopularFeed() {
  return useQuery({
    queryKey: POPULAR_KEY,
    queryFn: () => postApi.popular(),
    refetchInterval: 30000,
  })
}

export function useTrendingKeywords() {
  return useQuery({
    queryKey: ['trending-keywords'],
    queryFn: () => postApi.trendingKeywords(),
    refetchInterval: 30000,
  })
}

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
      queryClient.invalidateQueries({ queryKey: FEED_KEY })
    },
  })
}
