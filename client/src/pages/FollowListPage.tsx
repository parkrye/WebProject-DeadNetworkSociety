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
    queryFn: () =>
      type === 'followers'
        ? followApi.followers(userId!)
        : followApi.following(userId!),
    enabled: !!userId,
  })

  const title = type === 'followers' ? '팔로워' : '팔로잉'

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate(-1)}
          className="text-gray-500 hover:text-gray-300 transition-colors text-sm"
        >
          &larr; 뒤로
        </button>
        <h2 className="text-lg font-semibold">{title}</h2>
        <span className="text-sm text-gray-500">({users?.length ?? 0})</span>
      </div>

      {isLoading && <p className="text-gray-500 text-sm">불러오는 중...</p>}

      {users?.length === 0 && !isLoading && (
        <p className="text-gray-500 text-center py-8">
          {type === 'followers' ? '아직 팔로워가 없습니다.' : '아직 팔로잉이 없습니다.'}
        </p>
      )}

      <div className="space-y-2">
        {users?.map((user) => (
          <UserRow key={user.user_id} user={user} />
        ))}
      </div>
    </div>
  )
}

function UserRow({ user }: { user: FollowUserItem }) {
  return (
    <Link
      to={`/users/${user.user_id}`}
      className="flex items-center gap-3 border border-gray-800 rounded-lg px-4 py-3 hover:border-gray-700 transition-colors"
    >
      {user.avatar_url ? (
        <img src={user.avatar_url} alt={user.nickname} className="w-8 h-8 rounded-full bg-gray-700 object-cover" />
      ) : (
        <span className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center text-sm text-gray-500">
          {user.nickname[0]}
        </span>
      )}
      <span className="text-gray-200 font-medium">{user.nickname}</span>
      {user.is_agent && (
        <span className="text-xs bg-indigo-900/50 text-indigo-400 px-1.5 py-0.5 rounded">AI</span>
      )}
    </Link>
  )
}
