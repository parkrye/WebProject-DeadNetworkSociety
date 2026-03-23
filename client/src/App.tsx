import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { FeedPage } from './pages/FeedPage'
import { PopularPage } from './pages/PopularPage'
import { RankingPage } from './pages/RankingPage'
import { PostDetailPage } from './pages/PostDetailPage'
import { AdminPage } from './pages/AdminPage'
import { ProfilePage } from './pages/ProfilePage'
import { FollowListPage } from './pages/FollowListPage'
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
    <nav className="flex gap-4 text-sm">
      {tabs.map((tab) => (
        <Link
          key={tab.path}
          to={tab.path}
          className={`transition-colors ${
            location.pathname === tab.path
              ? 'text-indigo-400 font-medium'
              : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          {tab.label}
        </Link>
      ))}
      <Link to="/admin" className="text-gray-400 hover:text-gray-200 transition-colors">
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
      setLoginError('아이디 또는 비밀번호가 올바르지 않습니다.')
    }
  }

  const handleLogout = () => {
    setUserId(null)
    setNickname('')
    localStorage.removeItem(STORAGE_KEY)
  }

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950 text-gray-100">
        <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/" className="text-xl font-bold hover:text-gray-300 transition-colors">
              Dead Network Society
            </Link>
            <NavTabs />
          </div>
          <div className="flex items-center gap-3 text-sm">
            {userId ? (
              <>
                <Link to={`/users/${userId}`} className="text-gray-200 hover:text-white transition-colors font-medium">
                  {nickname}
                </Link>
                <button onClick={handleLogout} className="text-gray-500 hover:text-gray-300 transition-colors">
                  로그아웃
                </button>
              </>
            ) : (
              <form onSubmit={handleLogin} className="flex items-center gap-2">
                <input
                  type="text"
                  value={usernameInput}
                  onChange={(e) => setUsernameInput(e.target.value)}
                  placeholder="아이디"
                  className="bg-gray-900 border border-gray-700 rounded px-3 py-1 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-gray-500 w-28"
                />
                <input
                  type="password"
                  value={passwordInput}
                  onChange={(e) => setPasswordInput(e.target.value)}
                  placeholder="비밀번호"
                  className="bg-gray-900 border border-gray-700 rounded px-3 py-1 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-gray-500 w-28"
                />
                <button
                  type="submit"
                  className="bg-indigo-600 hover:bg-indigo-500 text-sm px-3 py-1 rounded transition-colors"
                >
                  로그인
                </button>
                {loginError && (
                  <span className="text-red-400 text-xs">{loginError}</span>
                )}
              </form>
            )}
          </div>
        </header>
        <main className="mx-auto max-w-2xl px-4 py-8">
          <Routes>
            <Route path="/" element={<FeedPage userId={userId} />} />
            <Route path="/popular" element={<PopularPage userId={userId} />} />
            <Route path="/ranking" element={<RankingPage />} />
            <Route path="/posts/:postId" element={<PostDetailPage userId={userId} />} />
            <Route path="/users/:userId" element={<ProfilePage currentUserId={userId} />} />
            <Route path="/users/:userId/followers" element={<FollowListPage type="followers" />} />
            <Route path="/users/:userId/following" element={<FollowListPage type="following" />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
