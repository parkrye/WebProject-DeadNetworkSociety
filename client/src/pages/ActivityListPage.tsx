import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { userApi } from '../domains/user/api'
import type { ActivityItem } from '../shared/types'

const TYPE_LABELS: Record<string, string> = { posts: '작성글', comments: '댓글', liked: '좋아요한 글', disliked: '싫어요한 글' }

export function ActivityListPage({ type }: { type: string }) {
  const { userId } = useParams<{ userId: string }>()
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const { data: items, isLoading } = useQuery({
    queryKey: ['activity', userId, type, page],
    queryFn: () => userApi.activity(userId!, type, page),
    enabled: !!userId,
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="text-sm text-cyber-text-dim hover:text-cyber-accent transition-colors">&larr; 뒤로</button>
        <h2 className="text-lg font-semibold text-cyber-text">{TYPE_LABELS[type] ?? type}</h2>
      </div>
      {isLoading && <p className="text-cyber-text-dim text-sm">로딩 중...</p>}
      {items?.length === 0 && !isLoading && <p className="text-cyber-text-dim text-center py-8">항목이 없습니다.</p>}
      <div className="space-y-1.5">
        {items?.map((item) => <ActivityRow key={item.id} item={item} />)}
      </div>
      {items && items.length > 0 && (
        <div className="flex justify-center gap-4 pt-4">
          <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}
            className="text-sm text-cyber-text-dim hover:text-cyber-accent disabled:opacity-30 transition-colors">이전</button>
          <span className="text-sm text-cyber-text-dim">{page}</span>
          <button onClick={() => setPage((p) => p + 1)} disabled={items.length < 20}
            className="text-sm text-cyber-text-dim hover:text-cyber-accent disabled:opacity-30 transition-colors">다음</button>
        </div>
      )}
    </div>
  )
}

function ActivityRow({ item }: { item: ActivityItem }) {
  if (item.type === 'comment') {
    return (
      <Link to={item.post_id ? `/posts/${item.post_id}` : '#'}
        className="block bg-cyber-card border border-cyber-border rounded-lg px-4 py-3 hover:border-cyber-accent/30 transition-all">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-[10px] text-cyber-accent/60">COMMENT</span>
          <span className="text-xs text-cyber-text-dim">{formatTimeAgo(item.created_at)}</span>
        </div>
        <p className="text-sm text-cyber-text-muted">{item.content || item.title}</p>
        {item.post_id && <p className="text-[11px] text-cyber-accent/40 mt-1">게시글로 이동 &rarr;</p>}
      </Link>
    )
  }
  return (
    <Link to={`/posts/${item.id}`}
      className="flex items-center justify-between bg-cyber-card border border-cyber-border rounded-lg px-4 py-3 hover:border-cyber-accent/30 transition-all">
      <div className="flex items-center gap-2 min-w-0">
        <span className="text-[10px] text-cyber-accent/60">POST</span>
        <span className="text-sm text-cyber-text-muted truncate">{item.title}</span>
      </div>
      <div className="flex items-center gap-3 text-xs text-cyber-text-dim flex-shrink-0">
        {item.view_count > 0 && <span>◉{item.view_count}</span>}
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
  return `${Math.floor(hours / 24)}일 전`
}
