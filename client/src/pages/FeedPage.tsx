import { useState } from 'react'
import { usePosts, useCreatePost } from '../domains/post/hooks'
import { PostCard } from '../domains/post/PostCard'

interface FeedPageProps {
  userId: string | null
}

export function FeedPage({ userId }: FeedPageProps) {
  const [page, setPage] = useState(1)
  const { data: posts, isLoading } = usePosts(page)
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

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Feed</h2>
        {userId && (
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-indigo-600 hover:bg-indigo-500 text-sm px-4 py-2 rounded transition-colors"
          >
            {showForm ? 'Cancel' : 'New Post'}
          </button>
        )}
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="space-y-3 border border-gray-800 rounded-lg p-4">
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Title"
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-gray-500"
          />
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="What's on your mind?"
            rows={4}
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-gray-500 resize-none"
          />
          <button
            type="submit"
            disabled={!title.trim() || !content.trim() || createMutation.isPending}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-sm px-4 py-2 rounded transition-colors"
          >
            {createMutation.isPending ? 'Posting...' : 'Post'}
          </button>
        </form>
      )}

      {isLoading && <p className="text-gray-500">Loading posts...</p>}

      <div className="space-y-3">
        {posts?.map((post) => (
          <PostCard key={post.id} post={post} userId={userId} />
        ))}
      </div>

      {posts && posts.length > 0 && (
        <div className="flex justify-center gap-4 pt-4">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="text-sm text-gray-400 hover:text-gray-200 disabled:opacity-30"
          >
            Previous
          </button>
          <span className="text-sm text-gray-500">Page {page}</span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={posts.length < 20}
            className="text-sm text-gray-400 hover:text-gray-200 disabled:opacity-30"
          >
            Next
          </button>
        </div>
      )}

      {posts?.length === 0 && !isLoading && (
        <p className="text-gray-500 text-center py-8">No posts yet. Be the first to post!</p>
      )}
    </div>
  )
}
