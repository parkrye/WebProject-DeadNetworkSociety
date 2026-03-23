import { usePopularFeed } from '../domains/post/hooks'
import { PostCard } from '../domains/post/PostCard'

interface PopularPageProps {
  userId: string | null
}

export function PopularPage({ userId }: PopularPageProps) {
  const { data: posts, isLoading } = usePopularFeed()

  return (
    <div className="space-y-4">
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
  )
}
