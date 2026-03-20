import { useState } from 'react'
import type { Comment } from '../../shared/types'
import { useCommentsByPost, useCreateComment } from './hooks'

interface CommentListProps {
  postId: string
  userId: string | null
}

export function CommentList({ postId, userId }: CommentListProps) {
  const { data: comments, isLoading } = useCommentsByPost(postId)
  const createMutation = useCreateComment()
  const [newComment, setNewComment] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!userId || !newComment.trim()) return
    createMutation.mutate(
      { post_id: postId, author_id: userId, content: newComment.trim() },
      { onSuccess: () => setNewComment('') },
    )
  }

  if (isLoading) return <p className="text-gray-500 text-sm">Loading comments...</p>

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-gray-300">
        Comments ({comments?.length ?? 0})
      </h3>

      {userId && (
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Write a comment..."
            className="flex-1 bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-gray-500"
          />
          <button
            type="submit"
            disabled={!newComment.trim() || createMutation.isPending}
            className="bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-sm px-4 py-2 rounded transition-colors"
          >
            Post
          </button>
        </form>
      )}

      <div className="space-y-2">
        {comments?.map((comment) => (
          <CommentItem key={comment.id} comment={comment} />
        ))}
      </div>
    </div>
  )
}

function CommentItem({ comment }: { comment: Comment }) {
  const indent = Math.min(comment.depth, 4)

  return (
    <div
      className="border-l border-gray-800 pl-3 py-2"
      style={{ marginLeft: `${indent * 16}px` }}
    >
      <p className="text-sm text-gray-300">{comment.content}</p>
      <span className="text-xs text-gray-600">
        {formatTimeAgo(comment.created_at)}
      </span>
    </div>
  )
}

function formatTimeAgo(dateStr: string): string {
  const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000)
  if (seconds < 60) return 'just now'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}
