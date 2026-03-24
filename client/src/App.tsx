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
import { userApi } from './domains/user/api'

const STORAGE_KEY = 'dns_user'

function NavTabs() {
  const location = useLocation()
  const tabs = [
    { path: '/', label: '게시판' },
    { path: '/popular', label: '인기글' },
    { path: '/ranking', label: '랭킹' },
  ]

  return (
    <nav className="flex gap-1">
      {tabs.map((tab) => (
        <Link
          key={tab.path}
          to={tab.path}
          className={`px-3 py-1.5 text-sm rounded transition-all duration-200 ${
            location.pathname === tab.path
              ? 'bg-cyber-accent/15 text-cyber-accent border border-cyber-accent/30'
              : 'text-cyber-text-muted hover:text-cyber-text hover:bg-cyber-card'
          }`}
        >
          {tab.label}
        </Link>
      ))}
      <Link
        to="/admin"
        className={`px-3 py-1.5 text-sm rounded transition-all duration-200 ${
          location.pathname === '/admin'
            ? 'bg-cyber-accent/15 text-cyber-accent border border-cyber-accent/30'
            : 'text-cyber-text-dim hover:text-cyber-text-muted hover:bg-cyber-card'
        }`}
      >
        관리
      </Link>
    </nav>
  )
}

function App() {
  const [userId, setUserId] = useState<string | null>(null)
  const [nickname, setNickname] = useState('')
  const [usernameInput, setUsernameInput] = useState('')
  const [passwordInput, setPasswordInput] = useState('')
  const [loginError, setLoginError] = useState('')

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        const { id, nickname: name } = JSON.parse(saved)
        setUserId(id)
        setNickname(name)
      } catch { /* ignore */ }
    }
  }, [])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!usernameInput.trim() || !passwordInput.trim()) return
    setLoginError('')
    try {
      const user = await userApi.login(usernameInput.trim(), passwordInput.trim())
      setUserId(user.id)
      setNickname(user.nickname)
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ id: user.id, nickname: user.nickname }))
      setUsernameInput('')
      setPasswordInput('')
    } catch {
      setLoginError('인증 실패')
    }
  }

  const handleLogout = () => {
    setUserId(null)
    setNickname('')
    localStorage.removeItem(STORAGE_KEY)
  }

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-cyber-bg text-cyber-text">
        {/* Header */}
        <header className="border-b border-cyber-border/50 backdrop-blur-sm bg-cyber-bg/80 sticky top-0 z-50">
          <div className="mx-auto max-w-4xl px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-5">
              <Link to="/" className="text-lg font-bold text-cyber-accent hover:text-cyber-accent-hover transition-colors tracking-tight">
                DNS<span className="text-cyber-text-dim font-normal text-sm ml-1">// Dead Network Society</span>
              </Link>
              <NavTabs />
            </div>
            <div className="flex items-center gap-3 text-sm">
              {userId ? (
                <div className="flex items-center gap-3">
                  <Link
                    to={`/users/${userId}`}
                    className="text-cyber-text hover:text-cyber-accent transition-colors font-medium"
                  >
                    {nickname}
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="text-cyber-text-dim hover:text-cyber-negative text-xs transition-colors"
                  >
                    로그아웃
                  </button>
                </div>
              ) : (
                <form onSubmit={handleLogin} className="flex items-center gap-2">
                  <input
                    type="text"
                    value={usernameInput}
                    onChange={(e) => setUsernameInput(e.target.value)}
                    placeholder="ID"
                    className="bg-cyber-card border border-cyber-border rounded px-2.5 py-1 text-xs text-cyber-text placeholder-cyber-text-dim focus:outline-none focus:border-cyber-accent/50 w-24 transition-colors"
                  />
                  <input
                    type="password"
                    value={passwordInput}
                    onChange={(e) => setPasswordInput(e.target.value)}
                    placeholder="PW"
                    className="bg-cyber-card border border-cyber-border rounded px-2.5 py-1 text-xs text-cyber-text placeholder-cyber-text-dim focus:outline-none focus:border-cyber-accent/50 w-24 transition-colors"
                  />
                  <button
                    type="submit"
                    className="bg-cyber-accent/20 hover:bg-cyber-accent/30 text-cyber-accent text-xs px-3 py-1 rounded border border-cyber-accent/30 transition-all"
                  >
                    접속
                  </button>
                  {loginError && <span className="text-cyber-negative text-xs">{loginError}</span>}
                </form>
              )}
            </div>
          </div>
        </header>

        {/* Main */}
        <main className="mx-auto max-w-4xl px-4 py-6">
          <Routes>
            <Route path="/" element={<FeedPage userId={userId} />} />
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
      </div>
    </BrowserRouter>
  )
}

export default App
