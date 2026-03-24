import { useParams, useNavigate } from 'react-router-dom'
import { usePost } from '../domains/post/hooks'
import { ReactionButtons } from '../domains/reaction/ReactionButtons'
import { CommentList } from '../domains/comment/CommentList'
import { AuthorLink } from '../shared/AuthorLink'
import { AdSlot } from '../shared/AdSlot'

interface PostDetailPageProps {
  userId: string | null
}

export function PostDetailPage({ userId }: PostDetailPageProps) {
  const { postId } = useParams<{ postId: string }>()
  const navigate = useNavigate()
  const { data: post, isLoading } = usePost(postId ?? '')

  if (isLoading) return <p className="text-cyber-text-dim">로딩 중...</p>
  if (!post) return <p className="text-cyber-text-dim">게시글을 찾을 수 없습니다.</p>

  return (
    <div className="space-y-6">
      <button onClick={() => navigate(-1)} className="text-sm text-cyber-text-dim hover:text-cyber-accent transition-colors">
        &larr; 뒤로
      </button>

      <article className="bg-cyber-card border border-cyber-border rounded-lg p-5">
        <h1 className="text-xl font-bold text-cyber-text mb-2">{post.title}</h1>
        <div className="flex items-center gap-3 text-xs text-cyber-text-dim mb-4">
          <AuthorLink
            authorId={post.author_id}
            nickname={post.author_nickname}
            avatarUrl={post.author_avatar_url}
            size="md"
          />
          <span>{new Date(post.created_at).toLocaleString('ko-KR')}</span>
        </div>
        <div className="text-cyber-text-muted whitespace-pre-wrap mb-3 leading-relaxed">{post.content}</div>
        {post.keywords && post.keywords.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {post.keywords.map((kw, i) => (
              <span key={i} className="text-xs text-cyber-accent/70 bg-cyber-accent/5 px-2 py-0.5 rounded">#{kw}</span>
            ))}
          </div>
        )}
        <ReactionButtons targetType="post" targetId={post.id} userId={userId} />
      </article>

      <AdSlot type="banner" />

      <div className="border-t border-cyber-border/50 pt-4">
        <CommentList postId={post.id} userId={userId} />
      </div>
    </div>
  )
}
