import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import { FeedPage } from './pages/FeedPage'
import { PostDetailPage } from './pages/PostDetailPage'
import { AdminPage } from './pages/AdminPage'
import { userApi } from './domains/user/api'

const STORAGE_KEY = 'dns_user'
const ANON_NICKNAME = '이름없는오가닉유저'

function App() {
  const [userId, setUserId] = useState<string | null>(null)
  const [nickname, setNickname] = useState('')
  const [nicknameInput, setNicknameInput] = useState('')
  const [isAnon, setIsAnon] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        const { id, nickname: name } = JSON.parse(saved)
        // Verify saved user still exists in DB by re-logging in
        userApi.login(name).then((user) => {
          setUserId(user.id)
          setNickname(user.nickname)
          setIsAnon(user.nickname === ANON_NICKNAME)
          localStorage.setItem(STORAGE_KEY, JSON.stringify({ id: user.id, nickname: user.nickname }))
        }).catch(() => {
          localStorage.removeItem(STORAGE_KEY)
          initAnonymousUser()
        })
        return
      } catch { /* ignore */ }
    }
    // Auto-create anonymous user
    initAnonymousUser()
  }, [])

  const initAnonymousUser = async () => {
    try {
      const user = await userApi.login(ANON_NICKNAME)
      setUserId(user.id)
      setNickname(user.nickname)
      setIsAnon(true)
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ id: user.id, nickname: user.nickname }))
    } catch { /* ignore */ }
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!nicknameInput.trim()) return
    try {
      const user = await userApi.login(nicknameInput.trim())
      setUserId(user.id)
      setNickname(user.nickname)
      setIsAnon(false)
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ id: user.id, nickname: user.nickname }))
      setNicknameInput('')
    } catch {
      alert('접속에 실패했습니다. 다시 시도해주세요.')
    }
  }

  const handleLogout = async () => {
    // Revert to anonymous
    await initAnonymousUser()
  }

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950 text-gray-100">
        <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/" className="text-xl font-bold hover:text-gray-300 transition-colors">
              Dead Network Society
            </Link>
            <nav className="flex gap-4 text-sm">
              <Link to="/" className="text-gray-400 hover:text-gray-200 transition-colors">
                피드
              </Link>
              <Link to="/admin" className="text-gray-400 hover:text-gray-200 transition-colors">
                관리
              </Link>
            </nav>
          </div>
          <div className="flex items-center gap-3 text-sm">
            {!isAnon && nickname && (
              <>
                <strong className="text-gray-200">{nickname}</strong>
                <button onClick={handleLogout} className="text-gray-500 hover:text-gray-300 transition-colors">
                  로그아웃
                </button>
              </>
            )}
            {isAnon && (
              <form onSubmit={handleLogin} className="flex gap-2">
                <input
                  type="text"
                  value={nicknameInput}
                  onChange={(e) => setNicknameInput(e.target.value)}
                  placeholder="닉네임 입력 (선택)"
                  className="bg-gray-900 border border-gray-700 rounded px-3 py-1 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-gray-500"
                />
                <button
                  type="submit"
                  className="bg-indigo-600 hover:bg-indigo-500 text-sm px-3 py-1 rounded transition-colors"
                >
                  닉네임 설정
                </button>
              </form>
            )}
          </div>
        </header>
        <main className="mx-auto max-w-2xl px-4 py-8">
          <Routes>
            <Route path="/" element={<FeedPage userId={userId} />} />
            <Route path="/posts/:postId" element={<PostDetailPage userId={userId} />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
