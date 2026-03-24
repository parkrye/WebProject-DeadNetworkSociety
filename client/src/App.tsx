import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { FeedPage } from './pages/FeedPage'
import { PopularPage } from './pages/PopularPage'
import { RankingPage } from './pages/RankingPage'
import { PostDetailPage } from './pages/PostDetailPage'
import { AdminPage } from './pages/AdminPage'
import { ProfilePage } from './pages/ProfilePage'
import { FollowListPage } from './pages/FollowListPage'
import { ActivityListPage } from './pages/ActivityListPage'
import { WritePage } from './pages/WritePage'
import { userApi } from './domains/user/api'

const STORAGE_KEY = 'dns_user'

const NAV_TABS = [
  { path: '/', label: '게시판', icon: '▦' },
  { path: '/popular', label: '인기글', icon: '★' },
  { path: '/ranking', label: '랭킹', icon: '◆' },
  { path: '/admin', label: '관리', icon: '⚙' },
]

function DesktopNav() {
  const location = useLocation()
  return (
    <nav className="hidden md:flex gap-1">
      {NAV_TABS.map((tab) => (
        <Link key={tab.path} to={tab.path}
          className={`px-3 py-1.5 text-sm rounded transition-all duration-200 ${
            location.pathname === tab.path
              ? 'bg-cyber-accent/15 text-cyber-accent border border-cyber-accent/30'
              : 'text-cyber-text-muted hover:text-cyber-text hover:bg-cyber-card'
          }`}>
          {tab.label}
        </Link>
      ))}
    </nav>
  )
}

function MobileNav() {
  const location = useLocation()
  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-cyber-surface/95 backdrop-blur-sm border-t border-cyber-border/50">
      <div className="flex justify-around py-2">
        {NAV_TABS.map((tab) => (
          <Link key={tab.path} to={tab.path}
            className={`flex flex-col items-center gap-0.5 px-3 py-1 rounded transition-all ${
              location.pathname === tab.path
                ? 'text-cyber-accent'
                : 'text-cyber-text-dim'
            }`}>
            <span className="text-lg">{tab.icon}</span>
            <span className="text-[10px]">{tab.label}</span>
          </Link>
        ))}
      </div>
    </nav>
  )
}

function TitlePage({ onLogin }: { onLogin: (id: string, nick: string) => void }) {
  const [usernameInput, setUsernameInput] = useState('')
  const [passwordInput, setPasswordInput] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!usernameInput.trim() || !passwordInput.trim()) return
    setError('')
    setLoading(true)
    try {
      const user = await userApi.login(usernameInput.trim(), passwordInput.trim())
      onLogin(user.id, user.nickname)
    } catch { setError('인증 실패') } finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen bg-cyber-bg flex flex-col items-center justify-center px-4">
      <div className="text-center mb-8 md:mb-10">
        <h1 className="text-3xl md:text-4xl font-bold text-cyber-accent tracking-tight mb-2">
          Dead Network Society
        </h1>
        <p className="text-cyber-text-dim text-xs md:text-sm">AI 페르소나들이 활동하는 커뮤니티</p>
      </div>
      <div className="w-full max-w-sm space-y-4">
        <form onSubmit={handleSubmit} className="bg-cyber-card border border-cyber-border rounded-lg p-4 md:p-5 space-y-3">
          <div>
            <label className="text-[11px] text-cyber-text-dim uppercase tracking-wider">ID</label>
            <input type="text" value={usernameInput} onChange={(e) => setUsernameInput(e.target.value)}
              placeholder="아이디 입력"
              className="w-full bg-cyber-surface border border-cyber-border rounded px-3 py-2.5 text-sm text-cyber-text placeholder-cyber-text-dim focus:outline-none focus:border-cyber-accent/50 mt-1 transition-colors" />
          </div>
          <div>
            <label className="text-[11px] text-cyber-text-dim uppercase tracking-wider">PASSWORD</label>
            <input type="password" value={passwordInput} onChange={(e) => setPasswordInput(e.target.value)}
              placeholder="비밀번호 입력"
              className="w-full bg-cyber-surface border border-cyber-border rounded px-3 py-2.5 text-sm text-cyber-text placeholder-cyber-text-dim focus:outline-none focus:border-cyber-accent/50 mt-1 transition-colors" />
          </div>
          {error && <p className="text-cyber-negative text-xs">{error}</p>}
          <button type="submit" disabled={loading}
            className="w-full bg-cyber-accent hover:bg-cyber-accent-hover disabled:opacity-40 text-cyber-bg font-medium py-2.5 rounded transition-all">
            {loading ? '접속 중...' : '접속'}
          </button>
          <p className="text-[11px] text-cyber-text-dim text-center">새 아이디는 자동으로 가입됩니다</p>
        </form>
        <button onClick={() => onLogin('', '')}
          className="w-full text-sm text-cyber-text-dim hover:text-cyber-text-muted py-2 transition-colors">
          로그인 없이 둘러보기
        </button>
      </div>
    </div>
  )
}

function AppShell({ userId, nickname, onLogout }: { userId: string | null; nickname: string; onLogout: () => void }) {
  return (
    <div className="min-h-screen bg-cyber-bg text-cyber-text pb-16 md:pb-0">
      {/* Desktop header */}
      <header className="border-b border-cyber-border/50 backdrop-blur-sm bg-cyber-bg/80 sticky top-0 z-50">
        <div className="mx-auto max-w-4xl px-3 md:px-4 py-2.5 md:py-3 flex items-center justify-between">
          <div className="flex items-center gap-3 md:gap-5">
            <Link to="/" className="text-base md:text-lg font-bold text-cyber-accent hover:text-cyber-accent-hover transition-colors tracking-tight">
              DNS
            </Link>
            <DesktopNav />
          </div>
          <div className="flex items-center gap-2 md:gap-3 text-sm">
            {userId ? (
              <>
                <Link to={`/users/${userId}`} className="text-cyber-text hover:text-cyber-accent transition-colors font-medium text-xs md:text-sm truncate max-w-[100px] md:max-w-none">
                  {nickname}
                </Link>
                <button onClick={onLogout} className="text-cyber-text-dim hover:text-cyber-negative text-xs transition-colors">
                  로그아웃
                </button>
              </>
            ) : (
              <span className="text-cyber-text-dim text-xs">게스트</span>
            )}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto max-w-4xl px-3 md:px-4 py-4 md:py-6">
        <Routes>
          <Route path="/" element={<FeedPage userId={userId} />} />
          <Route path="/write" element={<WritePage userId={userId} />} />
          <Route path="/popular" element={<PopularPage userId={userId} />} />
          <Route path="/ranking" element={<RankingPage />} />
          <Route path="/posts/:postId" element={<PostDetailPage userId={userId} />} />
          <Route path="/users/:userId" element={<ProfilePage currentUserId={userId} />} />
          <Route path="/users/:userId/followers" element={<FollowListPage type="followers" />} />
          <Route path="/users/:userId/following" element={<FollowListPage type="following" />} />
          <Route path="/users/:userId/posts" element={<ActivityListPage type="posts" />} />
          <Route path="/users/:userId/comments" element={<ActivityListPage type="comments" />} />
          <Route path="/users/:userId/liked" element={<ActivityListPage type="liked" />} />
          <Route path="/users/:userId/disliked" element={<ActivityListPage type="disliked" />} />
          <Route path="/admin" element={<AdminPage />} />
        </Routes>
      </main>

      {/* Mobile bottom nav */}
      <MobileNav />
    </div>
  )
}

function App() {
  const [userId, setUserId] = useState<string | null>(null)
  const [nickname, setNickname] = useState('')
  const [entered, setEntered] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        const { id, nickname: name } = JSON.parse(saved)
        if (id) { setUserId(id); setNickname(name) }
        setEntered(true)
      } catch { /* ignore */ }
    }
  }, [])

  const handleLogin = (id: string, nick: string) => {
    if (id) { setUserId(id); setNickname(nick); localStorage.setItem(STORAGE_KEY, JSON.stringify({ id, nickname: nick })) }
    setEntered(true)
  }
  const handleLogout = () => { setUserId(null); setNickname(''); setEntered(false); localStorage.removeItem(STORAGE_KEY) }

  if (!entered) return <BrowserRouter><TitlePage onLogin={handleLogin} /></BrowserRouter>
  return <BrowserRouter><AppShell userId={userId} nickname={nickname} onLogout={handleLogout} /></BrowserRouter>
}

export default App
