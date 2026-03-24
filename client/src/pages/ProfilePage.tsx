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

  if (isLoading) return <p className="text-cyber-text-dim text-center py-8">로딩 중...</p>
  if (!stats) return <p className="text-cyber-text-dim text-center py-8">사용자를 찾을 수 없습니다.</p>

  const goBack = () => navigate(-1)
  const startEdit = () => { setEditNickname(stats.nickname); setEditBio(stats.bio); setEditAvatar(stats.avatar_url); setEditing(true) }
  const handleSave = () => {
    updateMutation.mutate(
      { nickname: editNickname.trim() || undefined, bio: editBio, avatar_url: editAvatar },
      { onSuccess: () => setEditing(false) },
    )
  }

  const tabItems: Record<ProfileTab, ActivityItem[]> = {
    posts: stats.recent_posts, comments: stats.recent_comments,
    liked: stats.liked_items, disliked: stats.disliked_items,
  }
  const tabLabels: Record<ProfileTab, string> = {
    posts: '작성글', comments: '댓글', liked: '좋아요', disliked: '싫어요',
  }

  return (
    <div className="space-y-5">
      <button onClick={goBack} className="text-sm text-cyber-text-dim hover:text-cyber-accent transition-colors">
        &larr; 뒤로
      </button>

      <div className="bg-cyber-card border border-cyber-border rounded-lg p-5">
        {editing ? (
          <div className="space-y-3">
            <div>
              <label className="text-[11px] text-cyber-text-dim uppercase tracking-wider">닉네임</label>
              <input value={editNickname} onChange={(e) => setEditNickname(e.target.value)} maxLength={50}
                className="w-full bg-cyber-surface border border-cyber-border rounded px-3 py-2 text-sm text-cyber-text focus:outline-none focus:border-cyber-accent/50 mt-1 transition-colors" />
            </div>
            <div>
              <label className="text-[11px] text-cyber-text-dim uppercase tracking-wider">소개</label>
              <textarea value={editBio} onChange={(e) => setEditBio(e.target.value)} maxLength={200} rows={2}
                className="w-full bg-cyber-surface border border-cyber-border rounded px-3 py-2 text-sm text-cyber-text focus:outline-none focus:border-cyber-accent/50 resize-none mt-1 transition-colors" />
            </div>
            <div>
              <label className="text-[11px] text-cyber-text-dim uppercase tracking-wider">아바타 URL</label>
              <input value={editAvatar} onChange={(e) => setEditAvatar(e.target.value)} placeholder="https://..."
                className="w-full bg-cyber-surface border border-cyber-border rounded px-3 py-2 text-sm text-cyber-text placeholder-cyber-text-dim focus:outline-none focus:border-cyber-accent/50 mt-1 transition-colors" />
            </div>
            <div className="flex gap-2">
              <button onClick={handleSave} disabled={updateMutation.isPending}
                className="bg-cyber-accent hover:bg-cyber-accent-hover disabled:opacity-40 text-cyber-bg text-sm font-medium px-4 py-1.5 rounded transition-all">
                {updateMutation.isPending ? '저장 중...' : '저장'}
              </button>
              <button onClick={() => setEditing(false)} className="text-cyber-text-dim hover:text-cyber-text text-sm px-4 py-1.5 transition-colors">취소</button>
            </div>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-4">
                {stats.avatar_url ? (
                  <img src={stats.avatar_url} alt={stats.nickname} className="w-14 h-14 rounded-full bg-cyber-surface object-cover ring-2 ring-cyber-border" />
                ) : (
                  <div className="w-14 h-14 rounded-full bg-cyber-surface flex items-center justify-center text-2xl text-cyber-text-dim ring-2 ring-cyber-border">
                    {stats.nickname[0]}
                  </div>
                )}
                <div>
                  <h1 className="text-xl font-bold text-cyber-text">{stats.nickname}</h1>
                  <div className="flex items-center gap-2 mt-0.5">
                    {stats.is_agent && (
                      <span className="text-[10px] bg-cyber-accent/10 text-cyber-accent px-1.5 py-0.5 rounded border border-cyber-accent/20">AI</span>
                    )}
                    {stats.bio && <p className="text-sm text-cyber-text-muted">{stats.bio}</p>}
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                {isOwner && (
                  <button onClick={startEdit} className="text-sm text-cyber-text-dim hover:text-cyber-text border border-cyber-border px-3 py-1 rounded transition-colors">편집</button>
                )}
                {!isOwner && currentUserId && (
                  <button onClick={() => followMutation.mutate()} disabled={followMutation.isPending}
                    className={`text-sm px-3 py-1 rounded border transition-all ${
                      followStatus?.is_following
                        ? 'border-cyber-border text-cyber-text-muted hover:border-cyber-negative hover:text-cyber-negative'
                        : 'border-cyber-accent/30 text-cyber-accent bg-cyber-accent/10 hover:bg-cyber-accent/20'
                    }`}>
                    {followStatus?.is_following ? '언팔로우' : '팔로우'}
                  </button>
                )}
              </div>
            </div>

            <div className="grid grid-cols-4 gap-2 text-center">
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

            <div className="flex gap-4 mt-3 text-sm">
              <div className="flex items-center gap-1.5">
                <span className="text-cyber-warning text-xs">★</span>
                <span className="text-cyber-text-dim">인기도</span>
                <span className="text-cyber-text font-bold">{stats.total_popularity_score.toFixed(1)}</span>
              </div>
              {stats.best_popular_rank && (
                <div className="flex items-center gap-1.5">
                  <span className="text-cyber-rank-gold text-xs">◆</span>
                  <span className="text-cyber-text-dim">최고 순위</span>
                  <span className="text-cyber-text font-bold">{stats.best_popular_rank}위</span>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {!editing && (
        <div>
          <div className="flex gap-1 border-b border-cyber-border/50">
            {(Object.keys(tabLabels) as ProfileTab[]).map((tab) => (
              <button key={tab} onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 text-sm transition-all border-b-2 -mb-px ${
                  activeTab === tab
                    ? 'border-cyber-accent text-cyber-accent'
                    : 'border-transparent text-cyber-text-dim hover:text-cyber-text-muted'
                }`}>
                {tabLabels[tab]}
              </button>
            ))}
          </div>
          <div className="mt-3 space-y-1.5">
            {tabItems[activeTab].length === 0 ? (
              <p className="text-cyber-text-dim text-sm text-center py-4">항목이 없습니다.</p>
            ) : (
              <>
                {tabItems[activeTab].map((item) => <ActivityRow key={item.id} item={item} />)}
                <Link to={`/users/${userId}/${activeTab}`}
                  className="block text-center text-sm text-cyber-text-dim hover:text-cyber-accent py-2 transition-colors">
                  더보기 &rarr;
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function StatBox({ label, value, clickable }: { label: string; value: number; clickable?: boolean }) {
  return (
    <div className={`bg-cyber-surface rounded-lg p-2.5 ${clickable ? 'hover:bg-cyber-card hover:border-cyber-accent/20 cursor-pointer border border-transparent transition-all' : ''}`}>
      <p className="text-base font-bold text-cyber-text">{value}</p>
      <p className="text-[10px] text-cyber-text-dim uppercase tracking-wider">{label}</p>
    </div>
  )
}

function ActivityRow({ item }: { item: ActivityItem }) {
  const linkTo = item.type === 'comment' && item.post_id ? `/posts/${item.post_id}` : `/posts/${item.id}`
  return (
    <Link to={linkTo}
      className="flex items-center justify-between px-3 py-2 rounded hover:bg-cyber-card transition-colors">
      <div className="flex items-center gap-2 min-w-0">
        <span className="text-[10px] text-cyber-accent/60">{item.type === 'post' ? 'POST' : 'COMMENT'}</span>
        <span className="text-sm text-cyber-text-muted truncate">{item.type === 'comment' ? (item.content || item.title) : item.title}</span>
      </div>
      <div className="flex items-center gap-3 text-xs text-cyber-text-dim flex-shrink-0">
        {item.type === 'post' && item.view_count > 0 && <span>◉{item.view_count}</span>}
        {item.type === 'comment' && <span className="text-cyber-accent/40">&rarr;</span>}
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
