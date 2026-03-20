import { apiClient } from '../../shared/api-client'
import type { Post } from '../../shared/types'

export const postApi = {
  list: (page = 1, size = 20) =>
    apiClient.get<Post[]>(`/posts?page=${page}&size=${size}`),

  get: (id: string) =>
    apiClient.get<Post>(`/posts/${id}`),

  create: (data: { author_id: string; title: string; content: string }) =>
    apiClient.post<Post>('/posts', data),

  update: (id: string, data: { title?: string; content?: string }) =>
    apiClient.put<Post>(`/posts/${id}`, data),

  delete: (id: string) =>
    apiClient.delete<void>(`/posts/${id}`),
}
