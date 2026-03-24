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
      <h2 className="text-lg font-semibold">인기글</h2>

      {/* Trending keywords */}
      {keywords && keywords.length > 0 && (
        <div className="border border-gray-800 rounded-lg p-3">
          <h3 className="text-xs font-semibold text-gray-500 mb-2">인기 키워드</h3>
          <div className="flex flex-wrap gap-2">
            {keywords.map((kw, i) => (
              <span
                key={kw.keyword}
                className={`text-sm px-2 py-0.5 rounded-full border ${
                  i < 3
                    ? 'border-yellow-700 text-yellow-400 bg-yellow-900/20'
                    : 'border-gray-700 text-gray-400'
                }`}
              >
                {kw.keyword}
                <span className="text-xs text-gray-600 ml-1">{kw.count}</span>
              </span>
            ))}
          </div>
        </div>
      )}

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
  )
}
