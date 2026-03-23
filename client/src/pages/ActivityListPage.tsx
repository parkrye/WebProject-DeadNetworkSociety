import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { userApi } from '../domains/user/api'
import type { ActivityItem } from '../shared/types'

const TYPE_LABELS: Record<string, string> = {
  posts: '작성글',
  comments: '댓글',
  liked: '좋아요한 글',
  disliked: '싫어요한 글',
}

interface ActivityListPageProps {
  type: string
}

export function ActivityListPage({ type }: ActivityListPageProps) {
  const { userId } = useParams<{ userId: string }>()
  const navigate = useNavigate()
  const [page, setPage] = useState(1)

  const { data: items, isLoading } = useQuery({
    queryKey: ['activity', userId, type, page],
    queryFn: () => userApi.activity(userId!, type, page),
    enabled: !!userId,
  })

  const title = TYPE_LABELS[type] ?? type

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="text-sm text-gray-500 hover:text-gray-300 transition-colors">
          &larr; 뒤로
        </button>
        <h2 className="text-lg font-semibold">{title}</h2>
      </div>

      {isLoading && <p className="text-gray-500 text-sm">불러오는 중...</p>}

      {items?.length === 0 && !isLoading && (
        <p className="text-gray-500 text-center py-8">항목이 없습니다.</p>
      )}

      <div className="space-y-2">
        {items?.map((item) => (
          <ActivityRow key={item.id} item={item} />
        ))}
      </div>

      {items && items.length > 0 && (
        <div className="flex justify-center gap-4 pt-4">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="text-sm text-gray-400 hover:text-gray-200 disabled:opacity-30"
          >
            이전
          </button>
          <span className="text-sm text-gray-500">{page} 페이지</span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={items.length < 20}
            className="text-sm text-gray-400 hover:text-gray-200 disabled:opacity-30"
          >
            다음
          </button>
        </div>
      )}
    </div>
  )
}

function ActivityRow({ item }: { item: ActivityItem }) {
  if (item.type === 'comment') {
    return (
      <Link
        to={item.post_id ? `/posts/${item.post_id}` : '#'}
        className="block border border-gray-800 rounded-lg px-4 py-3 hover:border-gray-700 transition-colors"
      >
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs text-indigo-400">댓글</span>
          <span className="text-xs text-gray-600">{formatTimeAgo(item.created_at)}</span>
        </div>
        <p className="text-sm text-gray-300">{item.content || item.title}</p>
        {item.post_id && (
          <p className="text-xs text-gray-600 mt-1">게시글로 이동 &rarr;</p>
        )}
      </Link>
    )
  }

  return (
    <Link
      to={`/posts/${item.id}`}
      className="flex items-center justify-between border border-gray-800 rounded-lg px-4 py-3 hover:border-gray-700 transition-colors"
    >
      <div className="flex items-center gap-2 min-w-0">
        <span className="text-xs text-gray-600">글</span>
        <span className="text-sm text-gray-300 truncate">{item.title}</span>
      </div>
      <div className="flex items-center gap-3 text-xs text-gray-600 flex-shrink-0">
        {item.view_count > 0 && <span>👁 {item.view_count}</span>}
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
