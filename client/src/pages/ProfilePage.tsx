import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useUserStats, useUpdateUser } from '../domains/user/hooks'
import { useFollowStatus, useToggleFollow } from '../domains/follow/hooks'
import type { ActivityItem } from '../shared/types'

type ProfileTab = 'posts' | 'comments' | 'liked' | 'disliked'

interface ProfilePageProps {
  currentUserId: string | null
}

export function ProfilePage({ currentUserId }: ProfilePageProps) {
  const { userId } = useParams<{ userId: string }>()
  const navigate = useNavigate()
  const { data: stats, isLoading } = useUserStats(userId ?? '')
  const updateMutation = useUpdateUser(userId ?? '')
  const { data: followStatus } = useFollowStatus(userId ?? '', currentUserId)
  const followMutation = useToggleFollow(userId ?? '', currentUserId)
  const [activeTab, setActiveTab] = useState<ProfileTab>('posts')
  const [editing, setEditing] = useState(false)
  const [editNickname, setEditNickname] = useState('')
  const [editBio, setEditBio] = useState('')
  const [editAvatar, setEditAvatar] = useState('')

  const isOwner = currentUserId === userId

  if (isLoading) {
    return <p className="text-gray-500 text-center py-8">프로필을 불러오는 중...</p>
  }

  if (!stats) {
    return <p className="text-gray-500 text-center py-8">사용자를 찾을 수 없습니다.</p>
  }

  const goBack = () => navigate(-1)

  const startEdit = () => {
    setEditNickname(stats.nickname)
    setEditBio(stats.bio)
    setEditAvatar(stats.avatar_url)
    setEditing(true)
  }

  const handleSave = () => {
    updateMutation.mutate(
      {
        nickname: editNickname.trim() || undefined,
        bio: editBio,
        avatar_url: editAvatar,
      },
      { onSuccess: () => setEditing(false) },
    )
  }

  const tabItems: Record<ProfileTab, ActivityItem[]> = {
    posts: stats.recent_posts,
    comments: stats.recent_comments,
    liked: stats.liked_items,
    disliked: stats.disliked_items,
  }

  const tabLabels: Record<ProfileTab, string> = {
    posts: '작성글',
    comments: '댓글',
    liked: '좋아요',
    disliked: '싫어요',
  }

  return (
    <div className="space-y-6">
      <button onClick={goBack} className="text-sm text-gray-500 hover:text-gray-300 transition-colors">
        &larr; 뒤로
      </button>

      {/* Profile Header */}
      <div className="border border-gray-800 rounded-lg p-6">
        {editing ? (
          <div className="space-y-3">
            <div>
              <label className="text-xs text-gray-500">닉네임</label>
              <input
                value={editNickname}
                onChange={(e) => setEditNickname(e.target.value)}
                maxLength={50}
                className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-gray-500 mt-1"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500">소개</label>
              <textarea
                value={editBio}
                onChange={(e) => setEditBio(e.target.value)}
                maxLength={200}
                rows={2}
                className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-gray-500 resize-none mt-1"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500">아이콘 URL</label>
              <input
                value={editAvatar}
                onChange={(e) => setEditAvatar(e.target.value)}
                placeholder="https://..."
                className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-gray-500 mt-1"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleSave}
                disabled={updateMutation.isPending}
                className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-sm px-4 py-2 rounded transition-colors"
              >
                {updateMutation.isPending ? '저장 중...' : '저장'}
              </button>
              <button
                onClick={() => setEditing(false)}
                className="text-gray-400 hover:text-gray-200 text-sm px-4 py-2 transition-colors"
              >
                취소
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-4">
                {stats.avatar_url ? (
                  <img src={stats.avatar_url} alt={stats.nickname} className="w-14 h-14 rounded-full bg-gray-700 object-cover" />
                ) : (
                  <div className="w-14 h-14 rounded-full bg-gray-800 flex items-center justify-center text-2xl text-gray-500">
                    {stats.nickname[0]}
                  </div>
                )}
                <div>
                  <h1 className="text-xl font-bold text-gray-100">{stats.nickname}</h1>
                  {stats.is_agent && (
                    <span className="text-xs bg-indigo-900 text-indigo-300 px-2 py-0.5 rounded">AI</span>
                  )}
                  {stats.bio && <p className="text-sm text-gray-400 mt-1">{stats.bio}</p>}
                </div>
              </div>
              <div className="flex gap-2">
                {isOwner && (
                  <button
                    onClick={startEdit}
                    className="text-sm text-gray-400 hover:text-gray-200 border border-gray-700 px-3 py-1 rounded transition-colors"
                  >
                    편집
                  </button>
                )}
                {!isOwner && currentUserId && (
                  <button
                    onClick={() => followMutation.mutate()}
                    disabled={followMutation.isPending}
                    className={`text-sm px-3 py-1 rounded transition-colors ${
                      followStatus?.is_following
                        ? 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                        : 'bg-indigo-600 hover:bg-indigo-500 text-white'
                    }`}
                  >
                    {followStatus?.is_following ? '언팔로우' : '팔로우'}
                  </button>
                )}
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-4 gap-3 text-center">
              <Link to={`/users/${userId}/followers`}>
                <StatBox label="팔로워" value={stats.followers_count} clickable />
              </Link>
              <Link to={`/users/${userId}/following`}>
                <StatBox label="팔로잉" value={stats.following_count} clickable />
              </Link>
              <StatBox label="작성글" value={stats.post_count} />
              <StatBox label="댓글" value={stats.comment_count} />
              <StatBox label="좋아요 받음" value={stats.likes_received} />
              <StatBox label="좋아요 함" value={stats.likes_given} />
              <StatBox label="싫어요 받음" value={stats.dislikes_received} />
              <StatBox label="싫어요 함" value={stats.dislikes_given} />
            </div>

            {/* Popularity */}
            <div className="flex gap-4 mt-3 text-sm">
              <div className="flex items-center gap-2">
                <span className="text-yellow-500">★</span>
                <span className="text-gray-400">총 인기도</span>
                <span className="text-gray-100 font-bold">{stats.total_popularity_score.toFixed(1)}</span>
              </div>
              {stats.best_popular_rank && (
                <div className="flex items-center gap-2">
                  <span className="text-yellow-500">🏆</span>
                  <span className="text-gray-400">최고 순위</span>
                  <span className="text-gray-100 font-bold">{stats.best_popular_rank}위</span>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Activity Tabs */}
      {!editing && (
        <div>
          <div className="flex gap-1 border-b border-gray-800">
            {(Object.keys(tabLabels) as ProfileTab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                  activeTab === tab
                    ? 'border-indigo-500 text-indigo-400'
                    : 'border-transparent text-gray-500 hover:text-gray-300'
                }`}
              >
                {tabLabels[tab]}
              </button>
            ))}
          </div>

          <div className="mt-3 space-y-2">
            {tabItems[activeTab].length === 0 ? (
              <p className="text-gray-600 text-sm text-center py-4">항목이 없습니다.</p>
            ) : (
              tabItems[activeTab].map((item) => (
                <ActivityRow key={item.id} item={item} />
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function StatBox({ label, value, clickable }: { label: string; value: number; clickable?: boolean }) {
  return (
    <div className={`bg-gray-900 rounded-lg p-3 ${clickable ? 'hover:bg-gray-800 cursor-pointer transition-colors' : ''}`}>
      <p className="text-lg font-bold text-gray-100">{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  )
}

function ActivityRow({ item }: { item: ActivityItem }) {
  const linkTo = item.type === 'post' ? `/posts/${item.id}` : '#'

  return (
    <Link
      to={linkTo}
      className="flex items-center justify-between px-3 py-2 rounded hover:bg-gray-900 transition-colors"
    >
      <div className="flex items-center gap-2 min-w-0">
        <span className="text-xs text-gray-600">
          {item.type === 'post' ? '글' : '댓글'}
        </span>
        <span className="text-sm text-gray-300 truncate">{item.title}</span>
      </div>
      <div className="flex items-center gap-3 text-xs text-gray-600 flex-shrink-0">
        {item.type === 'post' && item.view_count > 0 && (
          <span>👁 {item.view_count}</span>
        )}
        <span>{formatTimeAgo(item.created_at)}</span>
      </div>
    </Link>
  )
}

function formatTimeAgo(dateStr: string): string {
  const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000)
  if (seconds < 60) return '방금'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}분 전`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}시간 전`
  const days = Math.floor(hours / 24)
  return `${days}일 전`
}
