import { useParams, useNavigate } from 'react-router-dom'
import { usePost } from '../domains/post/hooks'
import { ReactionButtons } from '../domains/reaction/ReactionButtons'
import { CommentList } from '../domains/comment/CommentList'
import { AuthorLink } from '../shared/AuthorLink'

interface PostDetailPageProps {
  userId: string | null
}

export function PostDetailPage({ userId }: PostDetailPageProps) {
  const { postId } = useParams<{ postId: string }>()
  const navigate = useNavigate()
  const { data: post, isLoading } = usePost(postId ?? '')

  if (isLoading) return <p className="text-gray-500">불러오는 중...</p>
  if (!post) return <p className="text-gray-500">게시글을 찾을 수 없습니다.</p>

  return (
    <div className="space-y-6">
      <button
        onClick={() => navigate(-1)}
        className="text-sm text-gray-500 hover:text-gray-300 transition-colors"
      >
        &larr; 뒤로
      </button>

      <article>
        <h1 className="text-2xl font-bold text-gray-100 mb-2">{post.title}</h1>
        <div className="flex items-center gap-3 text-xs text-gray-500 mb-4">
          <AuthorLink
            authorId={post.author_id}
            nickname={post.author_nickname}
            avatarUrl={post.author_avatar_url}
            size="md"
          />
          <span>{new Date(post.created_at).toLocaleString('ko-KR')}</span>
        </div>
        <div className="text-gray-300 whitespace-pre-wrap mb-3">{post.content}</div>
        {post.keywords && post.keywords.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {post.keywords.map((kw, i) => (
              <span key={i} className="text-sm text-indigo-400">#{kw}</span>
            ))}
          </div>
        )}
        <ReactionButtons targetType="post" targetId={post.id} userId={userId} />
      </article>

      <hr className="border-gray-800" />

      <CommentList postId={post.id} userId={userId} />
    </div>
  )
}
