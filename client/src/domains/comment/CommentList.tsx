import { useState } from 'react'
import type { Comment } from '../../shared/types'
import { useCommentsByPost, useCreateComment } from './hooks'
import { ReactionButtons } from '../reaction/ReactionButtons'
import { AuthorLink } from '../../shared/AuthorLink'

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

  if (isLoading) return <p className="text-cyber-text-dim text-sm">로딩 중...</p>

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-cyber-text-muted">
        댓글 ({comments?.length ?? 0})
      </h3>

      {userId && (
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="댓글을 입력하세요..."
            className="flex-1 bg-cyber-card border border-cyber-border rounded px-3 py-2 text-sm text-cyber-text placeholder-cyber-text-dim focus:outline-none focus:border-cyber-accent/50 transition-colors"
          />
          <button
            type="submit"
            disabled={!newComment.trim() || createMutation.isPending}
            className="bg-cyber-accent/20 hover:bg-cyber-accent/30 disabled:opacity-40 text-cyber-accent text-sm px-4 py-2 rounded border border-cyber-accent/30 transition-all"
          >
            작성
          </button>
        </form>
      )}

      <div className="space-y-0.5">
        {comments?.map((comment) => (
          <CommentItem key={comment.id} comment={comment} postId={postId} userId={userId} />
        ))}
      </div>
    </div>
  )
}

function CommentItem({ comment, postId, userId }: { comment: Comment; postId: string; userId: string | null }) {
  const [showReply, setShowReply] = useState(false)
  const [replyText, setReplyText] = useState('')
  const createMutation = useCreateComment()
  const indent = Math.min(comment.depth, 5)

  const handleReply = (e: React.FormEvent) => {
    e.preventDefault()
    if (!userId || !replyText.trim()) return
    createMutation.mutate(
      { post_id: postId, author_id: userId, content: replyText.trim(), parent_id: comment.id },
      { onSuccess: () => { setReplyText(''); setShowReply(false) } },
    )
  }

  return (
    <div className="border-l border-cyber-border/40 pl-3 py-2" style={{ marginLeft: `${indent * 16}px` }}>
      <div className="flex items-center gap-2 mb-1 text-xs">
        <AuthorLink authorId={comment.author_id} nickname={comment.author_nickname} avatarUrl={comment.author_avatar_url} />
        <span className="text-cyber-text-dim">{formatTimeAgo(comment.created_at)}</span>
      </div>

      <p className="text-sm text-cyber-text-muted mb-2 leading-relaxed">{comment.content}</p>

      <div className="flex items-center gap-3">
        <ReactionButtons targetType="comment" targetId={comment.id} userId={userId} />
        {userId && (
          <button onClick={() => setShowReply(!showReply)}
            className="text-xs text-cyber-text-dim hover:text-cyber-accent transition-colors">
            {showReply ? '취소' : '답글'}
          </button>
        )}
      </div>

      {showReply && (
        <form onSubmit={handleReply} className="flex gap-2 mt-2">
          <input type="text" value={replyText} onChange={(e) => setReplyText(e.target.value)}
            placeholder={`${comment.author_nickname}에게 답글...`} autoFocus
            className="flex-1 bg-cyber-card border border-cyber-border rounded px-2 py-1 text-xs text-cyber-text placeholder-cyber-text-dim focus:outline-none focus:border-cyber-accent/50 transition-colors" />
          <button type="submit" disabled={!replyText.trim() || createMutation.isPending}
            className="bg-cyber-accent/20 hover:bg-cyber-accent/30 disabled:opacity-40 text-cyber-accent text-xs px-3 py-1 rounded border border-cyber-accent/30 transition-all">
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
  return `${Math.floor(hours / 24)}일 전`
}
