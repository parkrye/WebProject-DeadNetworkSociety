import { Link } from 'react-router-dom'
import type { PostEnriched } from '../../shared/types'

interface PostCardProps {
  post: PostEnriched
  userId: string | null
}

export function PostCard({ post }: PostCardProps) {
  const timeAgo = formatTimeAgo(post.created_at)

  return (
    <article className="border border-gray-800 rounded-lg p-4 hover:border-gray-700 transition-colors">
      <Link to={`/posts/${post.id}`} className="block">
        <h2 className="text-lg font-semibold text-gray-100 mb-1">{post.title}</h2>
        <p className="text-gray-400 text-sm line-clamp-3 mb-3">{post.content}</p>
      </Link>
      <div className="flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center gap-3">
          {post.author_avatar_url && (
            <img
              src={post.author_avatar_url}
              alt={post.author_nickname}
              className="w-5 h-5 rounded-full bg-gray-700"
            />
          )}
          <span className="text-gray-400 font-medium">{post.author_nickname}</span>
          <span>{timeAgo}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1" title="Views">
            <span>👁</span> {post.view_count}
          </span>
          <span className="flex items-center gap-1" title="Comments">
            <span>💬</span> {post.comment_count}
          </span>
          <span className="flex items-center gap-1 text-green-500" title="Likes">
            <span>+</span>{post.like_count}
          </span>
          <span className="flex items-center gap-1 text-red-500" title="Dislikes">
            <span>-</span>{post.dislike_count}
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
