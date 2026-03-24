import { apiClient } from '../../shared/api-client'
import type { Post, PostEnriched, TrendingKeyword } from '../../shared/types'

export const postApi = {
  feed: (page = 1, size = 20) =>
    apiClient.get<PostEnriched[]>(`/posts/feed?page=${page}&size=${size}`),

  popular: () =>
    apiClient.get<PostEnriched[]>('/posts/popular'),

  search: (q: string, page = 1) =>
    apiClient.get<PostEnriched[]>(`/posts/search?q=${encodeURIComponent(q)}&page=${page}`),

  trendingKeywords: () =>
    apiClient.get<TrendingKeyword[]>('/posts/trending-keywords'),

  list: (page = 1, size = 20) =>
    apiClient.get<Post[]>(`/posts?page=${page}&size=${size}`),

  get: (id: string) =>
    apiClient.get<PostEnriched>(`/posts/${id}`),

  create: (data: { author_id: string; title: string; content: string }) =>
    apiClient.post<Post>('/posts', data),

  update: (id: string, data: { title?: string; content?: string }) =>
    apiClient.put<Post>(`/posts/${id}`, data),

  delete: (id: string) =>
    apiClient.delete<void>(`/posts/${id}`),
}
