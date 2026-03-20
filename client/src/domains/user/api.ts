import { apiClient } from '../../shared/api-client'
import type { User } from '../../shared/types'

export const userApi = {
  list: () => apiClient.get<User[]>('/users'),

  get: (id: string) => apiClient.get<User>(`/users/${id}`),

  create: (data: { nickname: string; is_agent?: boolean }) =>
    apiClient.post<User>('/users', data),
}
