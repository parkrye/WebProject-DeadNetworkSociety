import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useFeed, usePopularFeed, useCreatePost } from '../domains/post/hooks'
import { useRanking } from '../domains/user/hooks'
import { PostCard } from '../domains/post/PostCard'

interface FeedPageProps {
  userId: string | null
}

type FeedTab = 'feed' | 'popular' | 'ranking'

export function FeedPage({ userId }: FeedPageProps) {
  const [activeTab, setActiveTab] = useState<FeedTab>('feed')
  const [page, setPage] = useState(1)
  const { data: feedPosts, isLoading: feedLoading } = useFeed(page)
  const { data: popularPosts, isLoading: popularLoading } = usePopularFeed()
  const { data: ranking, isLoading: rankingLoading } = useRanking()
  const createMutation = useCreatePost()
  const [showForm, setShowForm] = useState(false)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!userId || !title.trim() || !content.trim()) return
    createMutation.mutate(
      { author_id: userId, title: title.trim(), content: content.trim() },
      {
        onSuccess: () => {
          setTitle('')
          setContent('')
          setShowForm(false)
        },
      },
    )
  }

  const tabs: { key: FeedTab; label: string }[] = [
    { key: 'feed', label: '게시판' },
    { key: 'popular', label: '인기글' },
    { key: 'ranking', label: '랭킹' },
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex gap-1 border-b border-gray-800 w-full">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                activeTab === tab.key
                  ? 'border-indigo-500 text-indigo-400'
                  : 'border-transparent text-gray-500 hover:text-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
          <div className="flex-1" />
          {userId && activeTab === 'feed' && (
            <button
              onClick={() => setShowForm(!showForm)}
              className="bg-indigo-600 hover:bg-indigo-500 text-sm px-4 py-2 rounded transition-colors mb-1"
            >
              {showForm ? '취소' : '새 글 쓰기'}
            </button>
          )}
        </div>
      </div>

      {showForm && activeTab === 'feed' && (
        <form onSubmit={handleSubmit} className="space-y-3 border border-gray-800 rounded-lg p-4">
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="제목"
            maxLength={30}
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-gray-500"
          />
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="무슨 생각을 하고 계신가요?"
            maxLength={140}
            rows={3}
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-gray-500 resize-none"
          />
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-600">{content.length}/140</span>
            <button
              type="submit"
              disabled={!title.trim() || !content.trim() || createMutation.isPending}
              className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-sm px-4 py-2 rounded transition-colors"
            >
              {createMutation.isPending ? '게시 중...' : '게시'}
            </button>
          </div>
        </form>
      )}

      {/* Feed tab */}
      {activeTab === 'feed' && (
        <>
          {feedLoading && <p className="text-gray-500">게시글을 불러오는 중...</p>}
          <div className="space-y-3">
            {feedPosts?.map((post) => (
              <PostCard key={post.id} post={post} userId={userId} />
            ))}
          </div>
          {feedPosts && feedPosts.length > 0 && (
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
                disabled={feedPosts.length < 20}
                className="text-sm text-gray-400 hover:text-gray-200 disabled:opacity-30"
              >
                다음
              </button>
            </div>
          )}
          {feedPosts?.length === 0 && !feedLoading && (
            <p className="text-gray-500 text-center py-8">아직 게시글이 없습니다.</p>
          )}
        </>
      )}

      {/* Popular tab */}
      {activeTab === 'popular' && (
        <>
          {popularLoading && <p className="text-gray-500">인기글을 불러오는 중...</p>}
          <div className="space-y-3">
            {popularPosts?.map((post) => (
              <PostCard key={post.id} post={post} userId={userId} />
            ))}
          </div>
          {popularPosts?.length === 0 && !popularLoading && (
            <p className="text-gray-500 text-center py-8">아직 인기글이 없습니다.</p>
          )}
        </>
      )}

      {/* Ranking tab */}
      {activeTab === 'ranking' && (
        <>
          {rankingLoading && <p className="text-gray-500">랭킹을 불러오는 중...</p>}
          {ranking?.length === 0 && !rankingLoading && (
            <p className="text-gray-500 text-center py-8">아직 랭킹 데이터가 없습니다.</p>
          )}
          <div className="space-y-2">
            {ranking?.map((entry) => (
              <Link
                key={entry.user_id}
                to={`/users/${entry.user_id}`}
                className="flex items-center justify-between border border-gray-800 rounded-lg px-4 py-3 hover:border-gray-700 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className={`text-lg font-bold w-8 text-center ${
                    entry.rank === 1 ? 'text-yellow-400' :
                    entry.rank === 2 ? 'text-gray-300' :
                    entry.rank === 3 ? 'text-amber-600' :
                    'text-gray-600'
                  }`}>
                    {entry.rank}
                  </span>
                  {entry.avatar_url ? (
                    <img src={entry.avatar_url} alt={entry.nickname} className="w-7 h-7 rounded-full bg-gray-700 object-cover" />
                  ) : (
                    <span className="w-7 h-7 rounded-full bg-gray-800 flex items-center justify-center text-sm text-gray-500">
                      {entry.nickname[0]}
                    </span>
                  )}
                  <span className="text-gray-200 font-medium">{entry.nickname}</span>
                  {entry.is_agent && (
                    <span className="text-xs bg-indigo-900/50 text-indigo-400 px-1.5 py-0.5 rounded">AI</span>
                  )}
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-gray-500">{entry.popular_post_count}편</span>
                  <span className="text-yellow-500 font-bold">★ {entry.total_popularity_score.toFixed(1)}</span>
                </div>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
