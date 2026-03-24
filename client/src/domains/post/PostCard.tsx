import { Link } from 'react-router-dom'
import type { PostEnriched } from '../../shared/types'
import { AuthorLink } from '../../shared/AuthorLink'

interface PostCardProps {
  post: PostEnriched
  userId: string | null
}

export function PostCard({ post }: PostCardProps) {
  const timeAgo = formatTimeAgo(post.created_at)

  return (
    <article className="bg-cyber-card border border-cyber-border rounded-lg p-4 hover:border-cyber-accent/30 transition-all duration-200 group">
      <Link to={`/posts/${post.id}`} className="block">
        <h2 className="text-[15px] font-semibold text-cyber-text mb-1 group-hover:text-cyber-accent transition-colors">{post.title}</h2>
        <p className="text-cyber-text-muted text-sm line-clamp-3 mb-2 leading-relaxed">{post.content}</p>
        {post.keywords && post.keywords.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-2">
            {post.keywords.map((kw, i) => (
              <span key={i} className="text-[11px] text-cyber-accent/70 bg-cyber-accent/5 px-1.5 py-0.5 rounded">#{kw}</span>
            ))}
          </div>
        )}
      </Link>
      <div className="flex flex-wrap items-center justify-between gap-y-1.5 text-xs text-cyber-text-dim">
        <div className="flex items-center gap-2 md:gap-3">
          <AuthorLink
            authorId={post.author_id}
            nickname={post.author_nickname}
            avatarUrl={post.author_avatar_url}
          />
          <span>{timeAgo}</span>
        </div>
        <div className="flex items-center gap-2.5">
          {post.popularity_score != null && (
            <span className="flex items-center gap-0.5 text-cyber-warning" title="인기도">
              <span className="text-[10px]">★</span>{post.popularity_score.toFixed(1)}
            </span>
          )}
          <span className="flex items-center gap-0.5" title="조회수">
            <span className="text-[10px]">◉</span>{post.view_count}
          </span>
          <span className="flex items-center gap-0.5" title="댓글">
            <span className="text-[10px]">◈</span>{post.comment_count}
          </span>
          <span className="flex items-center gap-0.5 text-cyber-positive" title="좋아요">
            +{post.like_count}
          </span>
          <span className="flex items-center gap-0.5 text-cyber-negative" title="싫어요">
            -{post.dislike_count}
          </span>
        </div>
      </div>
    </article>
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
