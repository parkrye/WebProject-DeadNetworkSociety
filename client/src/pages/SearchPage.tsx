import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useSearchPosts } from '../domains/post/hooks'
import { PostCard } from '../domains/post/PostCard'

interface SearchPageProps {
  userId: string | null
}

export function SearchPage({ userId }: SearchPageProps) {
  const [searchParams] = useSearchParams()
  const initialQuery = searchParams.get('q') ?? ''
  const [input, setInput] = useState(initialQuery)
  const [query, setQuery] = useState(initialQuery)
  const [page, setPage] = useState(1)
  const navigate = useNavigate()
  const { data: results, isLoading } = useSearchPosts(query, page)

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return
    setQuery(input.trim())
    setPage(1)
    navigate(`/search?q=${encodeURIComponent(input.trim())}`, { replace: true })
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="text-sm text-cyber-text-dim hover:text-cyber-accent transition-colors">&larr; 뒤로</button>
        <h2 className="text-lg font-semibold text-cyber-text">검색</h2>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="제목, 본문, 작성자, 태그 검색..."
          className="flex-1 bg-cyber-card border border-cyber-border rounded px-3 py-2 text-sm text-cyber-text placeholder-cyber-text-dim focus:outline-none focus:border-cyber-accent/50 transition-colors"
          autoFocus
        />
        <button type="submit"
          className="bg-cyber-accent/20 hover:bg-cyber-accent/30 text-cyber-accent text-sm px-4 py-2 rounded border border-cyber-accent/30 transition-all">
          검색
        </button>
      </form>

      {isLoading && <p className="text-cyber-text-dim text-sm">검색 중...</p>}

      {query && !isLoading && (
        <p className="text-xs text-cyber-text-dim">
          "{query}" 검색 결과 {results?.length ?? 0}건
        </p>
      )}

      <div className="space-y-3">
        {results?.map((post) => <PostCard key={post.id} post={post} userId={userId} />)}
      </div>

      {results && results.length > 0 && (
        <div className="flex justify-center gap-4 pt-4">
          <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}
            className="text-sm text-cyber-text-dim hover:text-cyber-accent disabled:opacity-30 transition-colors">이전</button>
          <span className="text-sm text-cyber-text-dim">{page}</span>
          <button onClick={() => setPage((p) => p + 1)} disabled={results.length < 20}
            className="text-sm text-cyber-text-dim hover:text-cyber-accent disabled:opacity-30 transition-colors">다음</button>
        </div>
      )}

      {query && results?.length === 0 && !isLoading && (
        <p className="text-cyber-text-dim text-center py-8">검색 결과가 없습니다.</p>
      )}
    </div>
  )
}
