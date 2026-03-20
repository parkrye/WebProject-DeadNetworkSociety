import { Link } from 'react-router-dom'
import type { Post } from '../../shared/types'
import { ReactionButtons } from '../reaction/ReactionButtons'

interface PostCardProps {
  post: Post
  userId: string | null
}

export function PostCard({ post, userId }: PostCardProps) {
  const timeAgo = formatTimeAgo(post.created_at)

  return (
    <article className="border border-gray-800 rounded-lg p-4 hover:border-gray-700 transition-colors">
      <Link to={`/posts/${post.id}`} className="block">
        <h2 className="text-lg font-semibold text-gray-100 mb-1">{post.title}</h2>
        <p className="text-gray-400 text-sm line-clamp-3 mb-3">{post.content}</p>
      </Link>
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>{timeAgo}</span>
        <ReactionButtons targetType="post" targetId={post.id} userId={userId} />
      </div>
    </article>
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
