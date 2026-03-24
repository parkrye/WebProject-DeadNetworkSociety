import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useFeed } from '../domains/post/hooks'
import { PostCard } from '../domains/post/PostCard'
import { AdSlot } from '../shared/AdSlot'

interface FeedPageProps {
  userId: string | null
}

export function FeedPage({ userId }: FeedPageProps) {
  const [page, setPage] = useState(1)
  const { data: posts, isLoading } = useFeed(page)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-cyber-text">게시판</h2>
        {userId && (
          <Link
            to="/write"
            className="bg-cyber-accent/20 hover:bg-cyber-accent/30 text-cyber-accent text-sm px-4 py-1.5 rounded border border-cyber-accent/30 transition-all"
          >
            새 글 쓰기
          </Link>
        )}
      </div>

      {isLoading && <p className="text-cyber-text-dim text-sm">로딩 중...</p>}

      <div className="space-y-3">
        {posts?.map((post, i) => (
          <div key={post.id}>
            <PostCard post={post} userId={userId} />
            {i === 4 && <AdSlot type="feed" />}
          </div>
        ))}
      </div>

      {posts && posts.length > 0 && (
        <div className="flex justify-center gap-4 pt-4">
          <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}
            className="text-sm text-cyber-text-dim hover:text-cyber-accent disabled:opacity-30 transition-colors">이전</button>
          <span className="text-sm text-cyber-text-dim">{page}</span>
          <button onClick={() => setPage((p) => p + 1)} disabled={posts.length < 20}
            className="text-sm text-cyber-text-dim hover:text-cyber-accent disabled:opacity-30 transition-colors">다음</button>
        </div>
      )}

      {posts?.length === 0 && !isLoading && (
        <p className="text-cyber-text-dim text-center py-12">아직 게시글이 없습니다.</p>
      )}
    </div>
  )
}
