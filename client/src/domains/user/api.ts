import { apiClient } from '../../shared/api-client'
import type { RankingEntry, User, UserProfileStats } from '../../shared/types'

export const userApi = {
  list: () => apiClient.get<User[]>('/users'),

  get: (id: string) => apiClient.get<User>(`/users/${id}`),

  create: (data: { nickname: string; is_agent?: boolean }) =>
    apiClient.post<User>('/users', data),

  login: (username: string, password: string) =>
    apiClient.post<User>('/users/login', { username, password }),

  update: (id: string, data: { nickname?: string; bio?: string; avatar_url?: string }) =>
    apiClient.patch<User>(`/users/${id}`, data),

  stats: (userId: string) =>
    apiClient.get<UserProfileStats>(`/users/${userId}/stats`),

  ranking: () =>
    apiClient.get<RankingEntry[]>('/users/ranking'),
}
