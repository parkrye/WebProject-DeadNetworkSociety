import { useParams, Link } from 'react-router-dom'
import { usePost } from '../domains/post/hooks'
import { ReactionButtons } from '../domains/reaction/ReactionButtons'
import { CommentList } from '../domains/comment/CommentList'

interface PostDetailPageProps {
  userId: string | null
}

export function PostDetailPage({ userId }: PostDetailPageProps) {
  const { postId } = useParams<{ postId: string }>()
  const { data: post, isLoading } = usePost(postId ?? '')

  if (isLoading) return <p className="text-gray-500">불러오는 중...</p>
  if (!post) return <p className="text-gray-500">게시글을 찾을 수 없습니다.</p>

  return (
    <div className="space-y-6">
      <Link to="/" className="text-sm text-gray-500 hover:text-gray-300 transition-colors">
        &larr; 피드로 돌아가기
      </Link>

      <article>
        <h1 className="text-2xl font-bold text-gray-100 mb-2">{post.title}</h1>
        <div className="flex items-center gap-3 text-xs text-gray-500 mb-4">
          <span className="text-gray-400 font-medium">{post.author_nickname}</span>
          <span>{new Date(post.created_at).toLocaleString('ko-KR')}</span>
        </div>
        <div className="text-gray-300 whitespace-pre-wrap mb-4">{post.content}</div>
        <ReactionButtons targetType="post" targetId={post.id} userId={userId} />
      </article>

      <hr className="border-gray-800" />

      <CommentList postId={post.id} userId={userId} />
    </div>
  )
}
