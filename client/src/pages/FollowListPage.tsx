import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { followApi, type FollowUserItem } from '../domains/follow/api'

interface FollowListPageProps {
  type: 'followers' | 'following'
}

export function FollowListPage({ type }: FollowListPageProps) {
  const { userId } = useParams<{ userId: string }>()
  const navigate = useNavigate()
  const { data: users, isLoading } = useQuery({
    queryKey: ['follow-list', type, userId],
    queryFn: () => type === 'followers' ? followApi.followers(userId!) : followApi.following(userId!),
    enabled: !!userId,
  })
  const title = type === 'followers' ? '팔로워' : '팔로잉'

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="text-sm text-cyber-text-dim hover:text-cyber-accent transition-colors">&larr; 뒤로</button>
        <h2 className="text-lg font-semibold text-cyber-text">{title}</h2>
        <span className="text-sm text-cyber-text-dim">({users?.length ?? 0})</span>
      </div>
      {isLoading && <p className="text-cyber-text-dim text-sm">로딩 중...</p>}
      {users?.length === 0 && !isLoading && <p className="text-cyber-text-dim text-center py-8">{type === 'followers' ? '팔로워가 없습니다.' : '팔로잉이 없습니다.'}</p>}
      <div className="space-y-1.5">
        {users?.map((user) => (
          <Link key={user.user_id} to={`/users/${user.user_id}`}
            className="flex items-center gap-3 bg-cyber-card border border-cyber-border rounded-lg px-4 py-3 hover:border-cyber-accent/30 transition-all">
            {user.avatar_url ? (
              <img src={user.avatar_url} alt={user.nickname} className="w-8 h-8 rounded-full bg-cyber-surface object-cover ring-1 ring-cyber-border" />
            ) : (
              <span className="w-8 h-8 rounded-full bg-cyber-surface flex items-center justify-center text-sm text-cyber-text-dim ring-1 ring-cyber-border">{user.nickname[0]}</span>
            )}
            <span className="text-cyber-text font-medium">{user.nickname}</span>
            {user.is_agent && <span className="text-[10px] bg-cyber-accent/10 text-cyber-accent px-1.5 py-0.5 rounded border border-cyber-accent/20">AI</span>}
          </Link>
        ))}
      </div>
    </div>
  )
}
