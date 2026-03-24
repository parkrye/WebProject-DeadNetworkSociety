import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCreatePost, useTrendingKeywords } from '../domains/post/hooks'
import { AdSlot } from '../shared/AdSlot'

interface WritePageProps {
  userId: string | null
}

export function WritePage({ userId }: WritePageProps) {
  const navigate = useNavigate()
  const createMutation = useCreatePost()
  const { data: keywords } = useTrendingKeywords()
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [showKeywords, setShowKeywords] = useState(false)

  if (!userId) {
    return <div className="text-center py-12"><p className="text-cyber-text-dim">로그인 후 글을 작성할 수 있습니다.</p></div>
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim() || !content.trim()) return
    createMutation.mutate(
      { author_id: userId, title: title.trim(), content: content.trim() },
      { onSuccess: () => navigate('/') },
    )
  }

  const keywordPanel = keywords && keywords.length > 0 && (
    <div className="bg-cyber-card border border-cyber-border rounded-lg p-4">
      <h3 className="text-[11px] font-semibold text-cyber-text-dim uppercase tracking-wider mb-3">인기 키워드</h3>
      <div className="space-y-1.5">
        {keywords.map((kw, i) => (
          <div key={kw.keyword} className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2 min-w-0">
              <span className={`w-5 text-right text-xs font-mono ${i < 3 ? 'text-cyber-accent' : 'text-cyber-text-dim'}`}>{i + 1}</span>
              <button onClick={() => setContent(prev => prev + (prev ? ' ' : '') + kw.keyword)}
                className="text-cyber-text-muted hover:text-cyber-accent transition-colors truncate text-left" title="클릭하여 본문에 추가">
                {kw.keyword}
              </button>
            </div>
            <span className="text-xs text-cyber-text-dim shrink-0">{kw.count}</span>
          </div>
        ))}
      </div>
      <p className="text-[10px] text-cyber-text-dim mt-3">키워드를 클릭하면 본문에 추가됩니다</p>
    </div>
  )

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="text-sm text-cyber-text-dim hover:text-cyber-accent transition-colors">&larr; 뒤로</button>
        <h2 className="text-lg font-semibold text-cyber-text">새 글 쓰기</h2>
      </div>

      {/* Mobile: collapsible keywords */}
      {keywords && keywords.length > 0 && (
        <div className="md:hidden">
          <button onClick={() => setShowKeywords(!showKeywords)}
            className="text-xs text-cyber-accent/70 hover:text-cyber-accent transition-colors">
            {showKeywords ? '인기 키워드 닫기 ▲' : '인기 키워드 보기 ▼'}
          </button>
          {showKeywords && <div className="mt-2">{keywordPanel}</div>}
        </div>
      )}

      <div className="flex gap-5">
        {/* Write form */}
        <form onSubmit={handleSubmit} className="flex-1 bg-cyber-card border border-cyber-border rounded-lg p-4 md:p-5 space-y-4">
          <div>
            <label className="text-[11px] text-cyber-text-dim uppercase tracking-wider">제목</label>
            <input type="text" value={title} onChange={(e) => setTitle(e.target.value)}
              placeholder="제목을 입력하세요" maxLength={30}
              className="w-full bg-cyber-surface border border-cyber-border rounded px-3 py-2.5 text-sm text-cyber-text placeholder-cyber-text-dim focus:outline-none focus:border-cyber-accent/50 mt-1 transition-colors" />
            <p className="text-[11px] text-cyber-text-dim mt-1 text-right">{title.length}/30</p>
          </div>
          <div>
            <label className="text-[11px] text-cyber-text-dim uppercase tracking-wider">본문</label>
            <textarea value={content} onChange={(e) => setContent(e.target.value)}
              placeholder="무슨 생각을 하고 계신가요?" maxLength={140} rows={5}
              className="w-full bg-cyber-surface border border-cyber-border rounded px-3 py-2.5 text-sm text-cyber-text placeholder-cyber-text-dim focus:outline-none focus:border-cyber-accent/50 resize-none mt-1 transition-colors" />
            <p className="text-[11px] text-cyber-text-dim mt-1 text-right">{content.length}/140</p>
          </div>
          <button type="submit" disabled={!title.trim() || !content.trim() || createMutation.isPending}
            className="w-full bg-cyber-accent hover:bg-cyber-accent-hover disabled:opacity-40 text-cyber-bg font-medium py-2.5 rounded transition-all">
            {createMutation.isPending ? '전송 중...' : '게시'}
          </button>
        </form>

        {/* Desktop: sidebar keywords */}
        <div className="w-52 shrink-0 hidden md:block">
          <div className="sticky top-20">
            {keywordPanel}
            <AdSlot type="sidebar" />
          </div>
        </div>
      </div>
    </div>
  )
}
