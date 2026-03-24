import { usePopularFeed, useTrendingKeywords } from '../domains/post/hooks'
import { PostCard } from '../domains/post/PostCard'

interface PopularPageProps {
  userId: string | null
}

export function PopularPage({ userId }: PopularPageProps) {
  const { data: posts, isLoading } = usePopularFeed()
  const { data: keywords } = useTrendingKeywords()

  return (
    <div className="flex gap-6">
      {/* Main: Popular posts */}
      <div className="flex-1 space-y-4 min-w-0">
        <h2 className="text-lg font-semibold">인기글</h2>

        {isLoading && <p className="text-gray-500">인기글을 불러오는 중...</p>}

        <div className="space-y-3">
          {posts?.map((post, i) => (
            <div key={post.id} className="relative">
              <span className={`absolute -left-8 top-4 text-sm font-bold ${
                i === 0 ? 'text-yellow-400' : i === 1 ? 'text-gray-300' : i === 2 ? 'text-amber-600' : 'text-gray-600'
              }`}>
                {i + 1}
              </span>
              <PostCard post={post} userId={userId} />
            </div>
          ))}
        </div>

        {posts?.length === 0 && !isLoading && (
          <p className="text-gray-500 text-center py-8">아직 인기글이 없습니다.</p>
        )}
      </div>

      {/* Sidebar: Trending keywords */}
      {keywords && keywords.length > 0 && (
        <div className="w-48 shrink-0 hidden lg:block">
          <div className="border border-gray-800 rounded-lg p-4 sticky top-24">
            <h3 className="text-sm font-semibold text-gray-300 mb-3">인기 키워드</h3>
            <div className="space-y-1.5">
              {keywords.map((kw, i) => (
                <div key={kw.keyword} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className={`w-5 text-right font-mono ${
                      i < 3 ? 'text-yellow-500' : 'text-gray-600'
                    }`}>
                      {i + 1}
                    </span>
                    <span className="text-gray-300 truncate">{kw.keyword}</span>
                  </div>
                  <span className="text-xs text-gray-600 shrink-0">{kw.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
