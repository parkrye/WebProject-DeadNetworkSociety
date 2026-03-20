import { apiClient } from '../../shared/api-client'
import type { ReactionCounts } from '../../shared/types'

export interface ReactionDetail {
  user_id: string
  user_nickname: string
  reaction_type: string
  created_at: string
}

export const reactionApi = {
  toggle: (data: { user_id: string; target_type: string; target_id: string; reaction_type: string }) =>
    apiClient.post<unknown>('/reactions', data),

  getCounts: (targetType: string, targetId: string) =>
    apiClient.get<ReactionCounts>(`/reactions/counts/${targetType}/${targetId}`),

  getList: (targetType: string, targetId: string) =>
    apiClient.get<ReactionDetail[]>(`/reactions/list/${targetType}/${targetId}`),
}
