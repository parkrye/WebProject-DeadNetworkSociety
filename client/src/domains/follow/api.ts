import { apiClient } from '../../shared/api-client'

export interface FollowUserItem {
  user_id: string
  nickname: string
  avatar_url: string
  is_agent: boolean
}

export const followApi = {
  toggle: (followerId: string, followingId: string) =>
    apiClient.post('/follows', { follower_id: followerId, following_id: followingId }),

  check: (userId: string, viewerId: string) =>
    apiClient.get<{ is_following: boolean }>(`/follows/${userId}/check?viewer_id=${viewerId}`),

  followers: (userId: string) =>
    apiClient.get<FollowUserItem[]>(`/follows/${userId}/followers`),

  following: (userId: string) =>
    apiClient.get<FollowUserItem[]>(`/follows/${userId}/following`),
}
