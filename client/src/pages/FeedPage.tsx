import { useState } from 'react'
import { useFeed, useCreatePost } from '../domains/post/hooks'
import { PostCard } from '../domains/post/PostCard'

interface FeedPageProps {
  userId: string | null
}

export function FeedPage({ userId }: FeedPageProps) {
  const [page, setPage] = useState(1)
  const { data: posts, isLoading } = useFeed(page)
  const createMutation = useCreatePost()
  const [showForm, setShowForm] = useState(false)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!userId || !title.trim() || !content.trim()) return
    createMutation.mutate(
      { author_id: userId, title: title.trim(), content: content.trim() },
      { onSuccess: () => { setTitle(''); setContent(''); setShowForm(false) } },
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-cyber-text">게시판</h2>
        {userId && (
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-cyber-accent/20 hover:bg-cyber-accent/30 text-cyber-accent text-sm px-4 py-1.5 rounded border border-cyber-accent/30 transition-all"
          >
            {showForm ? '취소' : '새 글 쓰기'}
          </button>
        )}
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="space-y-3 bg-cyber-card border border-cyber-border rounded-lg p-4">
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="제목"
            maxLength={30}
            className="w-full bg-cyber-surface border border-cyber-border rounded px-3 py-2 text-sm text-cyber-text placeholder-cyber-text-dim focus:outline-none focus:border-cyber-accent/50 transition-colors"
          />
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="무슨 생각을 하고 계신가요?"
            maxLength={140}
            rows={3}
            className="w-full bg-cyber-surface border border-cyber-border rounded px-3 py-2 text-sm text-cyber-text placeholder-cyber-text-dim focus:outline-none focus:border-cyber-accent/50 resize-none transition-colors"
          />
          <div className="flex items-center justify-between">
            <span className="text-xs text-cyber-text-dim">{content.length}/140</span>
            <button
              type="submit"
              disabled={!title.trim() || !content.trim() || createMutation.isPending}
              className="bg-cyber-accent hover:bg-cyber-accent-hover disabled:opacity-40 text-cyber-bg text-sm font-medium px-4 py-1.5 rounded transition-all"
            >
              {createMutation.isPending ? '전송 중...' : '게시'}
            </button>
          </div>
        </form>
      )}

      {isLoading && <p className="text-cyber-text-dim text-sm">로딩 중...</p>}

      <div className="space-y-3">
        {posts?.map((post) => <PostCard key={post.id} post={post} userId={userId} />)}
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
