import { usePopularFeed, useTrendingKeywords } from '../domains/post/hooks'
import { PostCard } from '../domains/post/PostCard'

interface PopularPageProps {
  userId: string | null
}

export function PopularPage({ userId }: PopularPageProps) {
  const { data: posts, isLoading } = usePopularFeed()
  const { data: keywords } = useTrendingKeywords()

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-cyber-text">인기글</h2>

      {/* Trending keywords */}
      {keywords && keywords.length > 0 && (
        <div className="bg-cyber-card border border-cyber-border rounded-lg p-3">
          <h3 className="text-[11px] font-semibold text-cyber-text-dim uppercase tracking-wider mb-2">Trending Keywords</h3>
          <div className="flex flex-wrap gap-1.5">
            {keywords.map((kw, i) => (
              <span
                key={kw.keyword}
                className={`text-xs px-2 py-0.5 rounded-full border transition-colors ${
                  i < 3
                    ? 'border-cyber-accent/40 text-cyber-accent bg-cyber-accent/10'
                    : 'border-cyber-border text-cyber-text-muted'
                }`}
              >
                {kw.keyword}
                <span className="text-cyber-text-dim ml-1">{kw.count}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {isLoading && <p className="text-cyber-text-dim text-sm">로딩 중...</p>}

      <div className="space-y-3">
        {posts?.map((post, i) => (
          <div key={post.id} className="flex gap-3 items-start">
            <span className={`w-7 pt-4 text-center text-sm font-bold shrink-0 ${
              i === 0 ? 'text-cyber-rank-gold' : i === 1 ? 'text-cyber-rank-silver' : i === 2 ? 'text-cyber-rank-bronze' : 'text-cyber-text-dim'
            }`}>
              {i + 1}
            </span>
            <div className="flex-1 min-w-0">
              <PostCard post={post} userId={userId} />
            </div>
          </div>
        ))}
      </div>

      {posts?.length === 0 && !isLoading && (
        <p className="text-cyber-text-dim text-center py-12">아직 인기글이 없습니다.</p>
      )}
    </div>
  )
}
