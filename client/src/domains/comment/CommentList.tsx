import { useState } from 'react'
import type { Comment } from '../../shared/types'
import { useCommentsByPost, useCreateComment } from './hooks'
import { ReactionButtons } from '../reaction/ReactionButtons'

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
            placeholder="댓글을 입력하세요..."
            className="flex-1 bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-gray-500"
          />
          <button
            type="submit"
            disabled={!newComment.trim() || createMutation.isPending}
            className="bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-sm px-4 py-2 rounded transition-colors"
          >
            작성
          </button>
        </form>
      )}

      <div className="space-y-1">
        {comments?.map((comment) => (
          <CommentItem
            key={comment.id}
            comment={comment}
            postId={postId}
            userId={userId}
          />
        ))}
      </div>
    </div>
  )
}

function CommentItem({
  comment,
  postId,
  userId,
}: {
  comment: Comment
  postId: string
  userId: string | null
}) {
  const [showReply, setShowReply] = useState(false)
  const [replyText, setReplyText] = useState('')
  const createMutation = useCreateComment()
  const indent = Math.min(comment.depth, 5)

  const handleReply = (e: React.FormEvent) => {
    e.preventDefault()
    if (!userId || !replyText.trim()) return
    createMutation.mutate(
      {
        post_id: postId,
        author_id: userId,
        content: replyText.trim(),
        parent_id: comment.id,
      },
      {
        onSuccess: () => {
          setReplyText('')
          setShowReply(false)
        },
      },
    )
  }

  return (
    <div
      className="border-l border-gray-800 pl-3 py-2"
      style={{ marginLeft: `${indent * 20}px` }}
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs font-medium text-gray-400">
          {comment.author_nickname}
        </span>
        <span className="text-xs text-gray-600">
          {formatTimeAgo(comment.created_at)}
        </span>
      </div>

      <p className="text-sm text-gray-300 mb-2">{comment.content}</p>

      <div className="flex items-center gap-3">
        <ReactionButtons targetType="comment" targetId={comment.id} userId={userId} />
        {userId && (
          <button
            onClick={() => setShowReply(!showReply)}
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            {showReply ? '취소' : '답글'}
          </button>
        )}
      </div>

      {showReply && (
        <form onSubmit={handleReply} className="flex gap-2 mt-2">
          <input
            type="text"
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            placeholder={`${comment.author_nickname}에게 답글...`}
            className="flex-1 bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs text-gray-100 placeholder-gray-600 focus:outline-none focus:border-gray-500"
            autoFocus
          />
          <button
            type="submit"
            disabled={!replyText.trim() || createMutation.isPending}
            className="bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-xs px-3 py-1 rounded transition-colors"
          >
            작성
          </button>
        </form>
      )}
    </div>
  )
}

function formatTimeAgo(dateStr: string): string {
  const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000)
  if (seconds < 60) return '방금'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}분 전`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}시간 전`
  const days = Math.floor(hours / 24)
  return `${days}일 전`
}
