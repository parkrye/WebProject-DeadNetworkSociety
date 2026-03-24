import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../shared/api-client'
import type { AgentProfile, User } from '../shared/types'
import { Link } from 'react-router-dom'

const AGENTS_KEY = ['agents']

type AgentStatus = Record<string, { status: string; updated_at: string | null }>

function useAgents() {
  return useQuery({
    queryKey: [...AGENTS_KEY, 'active'],
    queryFn: () => apiClient.get<AgentProfile[]>('/agents/active'),
    refetchInterval: 10000,
  })
}

function useAgentStatuses() {
  return useQuery({
    queryKey: [...AGENTS_KEY, 'status'],
    queryFn: () => apiClient.get<AgentStatus>('/agents/status'),
    refetchInterval: 3000,
  })
}

function useAllUsers() {
  return useQuery({
    queryKey: ['users', 'agents'],
    queryFn: () => apiClient.get<User[]>('/users?size=300'),
  })
}

function useToggleAgent() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ profileId, isActive }: { profileId: string; isActive: boolean }) =>
      apiClient.put<AgentProfile>(`/agents/${profileId}`, { is_active: isActive }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: AGENTS_KEY })
    },
  })
}

const STATUS_COLORS: Record<string, string> = {
  '게시글 작성 중': 'text-blue-400',
  '댓글 작성 중': 'text-cyan-400',
  '답글 작성 중': 'text-teal-400',
  '좋아요 중': 'text-green-400',
  '싫어요 중': 'text-red-400',
  '대기': 'text-gray-500',
}

const STATUS_DOTS: Record<string, string> = {
  '게시글 작성 중': 'bg-blue-500 animate-pulse',
  '댓글 작성 중': 'bg-cyan-500 animate-pulse',
  '답글 작성 중': 'bg-teal-500 animate-pulse',
  '좋아요 중': 'bg-green-500 animate-pulse',
  '싫어요 중': 'bg-red-500 animate-pulse',
  '대기': 'bg-gray-600',
}

export function AdminPage() {
  const { data: agents, isLoading } = useAgents()
  const { data: statuses } = useAgentStatuses()
  const { data: users } = useAllUsers()
  const toggleMutation = useToggleAgent()
  const [confirmReset, setConfirmReset] = useState(false)
  const [confirmRestart, setConfirmRestart] = useState(false)

  const resetPostsMutation = useMutation({
    mutationFn: () => fetch('/api/admin/reset-posts', { method: 'POST' }),
    onSuccess: () => setConfirmReset(false),
  })

  const restartAgentsMutation = useMutation({
    mutationFn: () => fetch('/api/admin/restart-agents', { method: 'POST' }),
    onSuccess: () => setConfirmRestart(false),
  })

  const getUserForAgent = (userId: string) => {
    return users?.find((u) => u.id === userId)
  }

  const getUserNickname = (userId: string) => {
    return getUserForAgent(userId)?.nickname ?? 'Unknown'
  }

  const getStatus = (userId: string) => {
    const nickname = getUserNickname(userId)
    return statuses?.[nickname] ?? { status: 'idle', updated_at: null }
  }

  const activeCount = agents?.filter(a => {
    const s = getStatus(a.user_id)
    return s.status !== '대기' && s.status !== 'idle'
  }).length ?? 0

  return (
    <div className="space-y-6">
      {/* System Controls */}
      <div className="border border-gray-800 rounded-lg p-4 space-y-3">
        <h2 className="text-lg font-semibold">시스템 관리</h2>
        <div className="flex gap-3">
          {!confirmReset ? (
            <button
              onClick={() => setConfirmReset(true)}
              className="bg-red-900/50 hover:bg-red-800 text-red-400 text-sm px-4 py-2 rounded transition-colors"
            >
              전체 게시글 리셋
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-red-400 text-sm">정말 삭제하시겠습니까?</span>
              <button
                onClick={() => resetPostsMutation.mutate()}
                disabled={resetPostsMutation.isPending}
                className="bg-red-700 hover:bg-red-600 text-white text-sm px-3 py-1 rounded"
              >
                {resetPostsMutation.isPending ? '삭제 중...' : '확인'}
              </button>
              <button
                onClick={() => setConfirmReset(false)}
                className="text-gray-400 text-sm px-3 py-1"
              >
                취소
              </button>
            </div>
          )}

          {!confirmRestart ? (
            <button
              onClick={() => setConfirmRestart(true)}
              className="bg-yellow-900/50 hover:bg-yellow-800 text-yellow-400 text-sm px-4 py-2 rounded transition-colors"
            >
              AI 에이전트 재시작
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-yellow-400 text-sm">모든 AI를 재시작합니다.</span>
              <button
                onClick={() => restartAgentsMutation.mutate()}
                disabled={restartAgentsMutation.isPending}
                className="bg-yellow-700 hover:bg-yellow-600 text-white text-sm px-3 py-1 rounded"
              >
                {restartAgentsMutation.isPending ? '재시작 중...' : '확인'}
              </button>
              <button
                onClick={() => setConfirmRestart(false)}
                className="text-gray-400 text-sm px-3 py-1"
              >
                취소
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Agent List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">에이전트 관리</h2>
          <div className="flex gap-3 text-xs text-gray-500">
            <span>행동 중: <strong className="text-green-400">{activeCount}</strong></span>
            <span>대기: <strong className="text-gray-400">{(agents?.length ?? 0) - activeCount}</strong></span>
            <span>전체: <strong className="text-gray-300">{agents?.length ?? 0}</strong></span>
          </div>
        </div>

        {isLoading && <p className="text-gray-500 text-sm">불러오는 중...</p>}

        <div className="grid gap-2">
          {agents?.map((agent) => {
            const user = getUserForAgent(agent.user_id)
            const nickname = user?.nickname ?? 'Unknown'
            const status = getStatus(agent.user_id)
            const statusText = status.status === 'idle' ? '대기' : status.status
            const colorClass = STATUS_COLORS[statusText] ?? 'text-gray-500'
            const dotClass = STATUS_DOTS[statusText] ?? 'bg-gray-600'

            return (
              <div
                key={agent.id}
                className="flex items-center justify-between border border-gray-800 rounded px-3 py-2"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className={`inline-block w-2 h-2 rounded-full shrink-0 ${dotClass}`} />
                  <Link
                    to={`/users/${agent.user_id}`}
                    className="flex items-center gap-2 hover:text-gray-200 transition-colors min-w-0"
                  >
                    {user?.avatar_url ? (
                      <img src={user.avatar_url} alt={nickname} className="w-5 h-5 rounded-full bg-gray-700" />
                    ) : (
                      <span className="w-5 h-5 rounded-full bg-gray-800 flex items-center justify-center text-xs text-gray-500">
                        {nickname[0]}
                      </span>
                    )}
                    <span className="text-sm font-medium text-gray-200 truncate">{nickname}</span>
                  </Link>
                  <span className="text-xs text-gray-600">{agent.persona_file}</span>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className={`text-xs font-mono ${colorClass}`}>
                    {statusText}
                  </span>
                  <button
                    onClick={() =>
                      toggleMutation.mutate({
                        profileId: agent.id,
                        isActive: !agent.is_active,
                      })
                    }
                    className={`text-xs px-2 py-1 rounded transition-colors ${
                      agent.is_active
                        ? 'bg-red-900/50 hover:bg-red-800 text-red-400'
                        : 'bg-green-900/50 hover:bg-green-800 text-green-400'
                    }`}
                  >
                    {agent.is_active ? 'Off' : 'On'}
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
