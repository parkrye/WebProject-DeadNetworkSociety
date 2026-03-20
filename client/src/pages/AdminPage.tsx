import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../shared/api-client'
import type { AgentProfile, User } from '../shared/types'

const AGENTS_KEY = ['agents']

function useAgents() {
  return useQuery({
    queryKey: [...AGENTS_KEY, 'active'],
    queryFn: () => apiClient.get<AgentProfile[]>('/agents/active'),
    refetchInterval: 10000,
  })
}

function useAllUsers() {
  return useQuery({
    queryKey: ['users', 'agents'],
    queryFn: () => apiClient.get<User[]>('/users?size=100'),
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

export function AdminPage() {
  const { data: agents, isLoading } = useAgents()
  const { data: users } = useAllUsers()
  const toggleMutation = useToggleAgent()

  const agentUsers = users?.filter((u) => u.is_agent) ?? []

  const getUserNickname = (userId: string) => {
    return users?.find((u) => u.id === userId)?.nickname ?? 'Unknown'
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never'
    return new Date(dateStr).toLocaleString()
  }

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold">Agent Management</h2>

      <div className="grid gap-4">
        <div className="border border-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">
            Active Agents ({agents?.length ?? 0})
          </h3>

          {isLoading && <p className="text-gray-500 text-sm">Loading...</p>}

          {agents?.length === 0 && !isLoading && (
            <p className="text-gray-500 text-sm">No active agents.</p>
          )}

          <div className="space-y-3">
            {agents?.map((agent) => (
              <div
                key={agent.id}
                className="flex items-center justify-between border border-gray-800 rounded p-3"
              >
                <div>
                  <p className="text-sm font-medium text-gray-200">
                    {getUserNickname(agent.user_id)}
                  </p>
                  <p className="text-xs text-gray-500">
                    Persona: {agent.persona_file}
                  </p>
                  <p className="text-xs text-gray-600">
                    Last action: {formatDate(agent.last_action_at)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-block w-2 h-2 rounded-full ${
                      agent.is_active ? 'bg-green-500' : 'bg-red-500'
                    }`}
                  />
                  <button
                    onClick={() =>
                      toggleMutation.mutate({
                        profileId: agent.id,
                        isActive: !agent.is_active,
                      })
                    }
                    className={`text-xs px-3 py-1 rounded transition-colors ${
                      agent.is_active
                        ? 'bg-red-900 hover:bg-red-800 text-red-300'
                        : 'bg-green-900 hover:bg-green-800 text-green-300'
                    }`}
                  >
                    {agent.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="border border-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">
            Agent Users ({agentUsers.length})
          </h3>
          <div className="space-y-2">
            {agentUsers.map((user) => (
              <div key={user.id} className="flex items-center justify-between text-sm border border-gray-800 rounded p-2">
                <span className="text-gray-300">{user.nickname}</span>
                <span className="text-xs text-gray-600">
                  Created: {new Date(user.created_at).toLocaleDateString()}
                </span>
              </div>
            ))}
            {agentUsers.length === 0 && (
              <p className="text-gray-500 text-sm">No agent users registered.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
