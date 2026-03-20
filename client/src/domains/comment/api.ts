import { apiClient } from '../../shared/api-client'
import type { Comment } from '../../shared/types'

export const commentApi = {
  listByPost: (postId: string, page = 1, size = 50) =>
    apiClient.get<Comment[]>(`/comments/by-post/${postId}?page=${page}&size=${size}`),

  create: (data: { post_id: string; author_id: string; content: string; parent_id?: string }) =>
    apiClient.post<Comment>('/comments', data),
}
