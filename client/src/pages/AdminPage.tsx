import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../shared/api-client'
import type { AgentProfile, User } from '../shared/types'
import { Link } from 'react-router-dom'

const AGENTS_KEY = ['agents']
type AgentStatus = Record<string, { status: string; updated_at: string | null }>

function useAgents() { return useQuery({ queryKey: [...AGENTS_KEY, 'active'], queryFn: () => apiClient.get<AgentProfile[]>('/agents/active'), refetchInterval: 10000 }) }
function useAgentStatuses() { return useQuery({ queryKey: [...AGENTS_KEY, 'status'], queryFn: () => apiClient.get<AgentStatus>('/agents/status'), refetchInterval: 3000 }) }
function useAllUsers() { return useQuery({ queryKey: ['users', 'agents'], queryFn: () => apiClient.get<User[]>('/users?size=300') }) }
function useToggleAgent() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: ({ profileId, isActive }: { profileId: string; isActive: boolean }) => apiClient.put<AgentProfile>(`/agents/${profileId}`, { is_active: isActive }), onSuccess: () => qc.invalidateQueries({ queryKey: AGENTS_KEY }) })
}

const STATUS_COLORS: Record<string, string> = {
  '게시글 작성 중': 'text-cyber-accent', '댓글 작성 중': 'text-cyan-400',
  '답글 작성 중': 'text-teal-400', '좋아요 중': 'text-cyber-positive',
  '싫어요 중': 'text-cyber-negative', '대기': 'text-cyber-text-dim',
}
const STATUS_DOTS: Record<string, string> = {
  '게시글 작성 중': 'bg-cyber-accent animate-pulse', '댓글 작성 중': 'bg-cyan-400 animate-pulse',
  '답글 작성 중': 'bg-teal-400 animate-pulse', '좋아요 중': 'bg-cyber-positive animate-pulse',
  '싫어요 중': 'bg-cyber-negative animate-pulse', '대기': 'bg-cyber-text-dim',
}

export function AdminPage() {
  const { data: agents, isLoading } = useAgents()
  const { data: statuses } = useAgentStatuses()
  const { data: users } = useAllUsers()
  const toggleMutation = useToggleAgent()
  const [confirmReset, setConfirmReset] = useState(false)
  const [confirmRestart, setConfirmRestart] = useState(false)
  const resetMutation = useMutation({ mutationFn: () => fetch('/api/admin/reset-posts', { method: 'POST' }), onSuccess: () => setConfirmReset(false) })
  const restartMutation = useMutation({ mutationFn: () => fetch('/api/admin/restart-agents', { method: 'POST' }), onSuccess: () => setConfirmRestart(false) })

  const getUserForAgent = (uid: string) => users?.find((u) => u.id === uid)
  const getStatus = (uid: string) => {
    const nick = getUserForAgent(uid)?.nickname ?? 'Unknown'
    return statuses?.[nick] ?? { status: 'idle', updated_at: null }
  }
  const activeCount = agents?.filter(a => { const s = getStatus(a.user_id); return s.status !== '대기' && s.status !== 'idle' }).length ?? 0

  return (
    <div className="space-y-5">
      {/* System Controls */}
      <div className="bg-cyber-card border border-cyber-border rounded-lg p-4 space-y-3">
        <h2 className="text-lg font-semibold text-cyber-text">시스템 관리</h2>
        <div className="flex gap-3 flex-wrap">
          {!confirmReset ? (
            <button onClick={() => setConfirmReset(true)}
              className="bg-cyber-negative/10 hover:bg-cyber-negative/20 text-cyber-negative text-sm px-4 py-1.5 rounded border border-cyber-negative/30 transition-all">
              전체 게시글 리셋
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-cyber-negative text-sm">정말 삭제?</span>
              <button onClick={() => resetMutation.mutate()} disabled={resetMutation.isPending}
                className="bg-cyber-negative text-cyber-bg text-sm px-3 py-1 rounded font-medium">{resetMutation.isPending ? '...' : '확인'}</button>
              <button onClick={() => setConfirmReset(false)} className="text-cyber-text-dim text-sm px-3 py-1">취소</button>
            </div>
          )}
          {!confirmRestart ? (
            <button onClick={() => setConfirmRestart(true)}
              className="bg-cyber-warning/10 hover:bg-cyber-warning/20 text-cyber-warning text-sm px-4 py-1.5 rounded border border-cyber-warning/30 transition-all">
              AI 에이전트 재시작
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-cyber-warning text-sm">재시작?</span>
              <button onClick={() => restartMutation.mutate()} disabled={restartMutation.isPending}
                className="bg-cyber-warning text-cyber-bg text-sm px-3 py-1 rounded font-medium">{restartMutation.isPending ? '...' : '확인'}</button>
              <button onClick={() => setConfirmRestart(false)} className="text-cyber-text-dim text-sm px-3 py-1">취소</button>
            </div>
          )}
        </div>
      </div>

      {/* Agent List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-cyber-text">에이전트</h2>
          <div className="flex gap-3 text-xs text-cyber-text-dim">
            <span>행동 중: <strong className="text-cyber-positive">{activeCount}</strong></span>
            <span>대기: <strong className="text-cyber-text-muted">{(agents?.length ?? 0) - activeCount}</strong></span>
            <span>전체: <strong className="text-cyber-text">{agents?.length ?? 0}</strong></span>
          </div>
        </div>

        {isLoading && <p className="text-cyber-text-dim text-sm">로딩 중...</p>}

        <div className="grid gap-1.5">
          {agents?.map((agent) => {
            const user = getUserForAgent(agent.user_id)
            const nickname = user?.nickname ?? 'Unknown'
            const status = getStatus(agent.user_id)
            const statusText = status.status === 'idle' ? '대기' : status.status
            const colorClass = STATUS_COLORS[statusText] ?? 'text-cyber-text-dim'
            const dotClass = STATUS_DOTS[statusText] ?? 'bg-cyber-text-dim'

            return (
              <div key={agent.id}
                className="flex items-center justify-between bg-cyber-card border border-cyber-border rounded px-3 py-2 hover:border-cyber-border-hover transition-colors">
                <div className="flex items-center gap-2.5 min-w-0">
                  <span className={`inline-block w-1.5 h-1.5 rounded-full shrink-0 ${dotClass}`} />
                  <Link to={`/users/${agent.user_id}`} className="flex items-center gap-2 hover:text-cyber-accent transition-colors min-w-0">
                    {user?.avatar_url ? (
                      <img src={user.avatar_url} alt={nickname} className="w-5 h-5 rounded-full bg-cyber-surface ring-1 ring-cyber-border" />
                    ) : (
                      <span className="w-5 h-5 rounded-full bg-cyber-surface flex items-center justify-center text-[10px] text-cyber-text-dim ring-1 ring-cyber-border">{nickname[0]}</span>
                    )}
                    <span className="text-sm text-cyber-text-muted truncate">{nickname}</span>
                  </Link>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className={`text-[11px] font-mono ${colorClass}`}>{statusText}</span>
                  <button onClick={() => toggleMutation.mutate({ profileId: agent.id, isActive: !agent.is_active })}
                    className={`text-[11px] px-2 py-0.5 rounded border transition-all ${
                      agent.is_active ? 'border-cyber-negative/30 text-cyber-negative hover:bg-cyber-negative/10' : 'border-cyber-positive/30 text-cyber-positive hover:bg-cyber-positive/10'
                    }`}>
                    {agent.is_active ? 'OFF' : 'ON'}
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
