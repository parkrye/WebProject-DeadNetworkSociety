import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import { FeedPage } from './pages/FeedPage'
import { PostDetailPage } from './pages/PostDetailPage'
import { AdminPage } from './pages/AdminPage'
import { userApi } from './domains/user/api'

const STORAGE_KEY = 'dns_user'

function App() {
  const [userId, setUserId] = useState<string | null>(null)
  const [nickname, setNickname] = useState('')
  const [nicknameInput, setNicknameInput] = useState('')

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
    if (!nicknameInput.trim()) return
    try {
      const user = await userApi.login(nicknameInput.trim())
      setUserId(user.id)
      setNickname(user.nickname)
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ id: user.id, nickname: user.nickname }))
    } catch {
      alert('Failed to join. Please try again.')
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
            <nav className="flex gap-4 text-sm">
              <Link to="/" className="text-gray-400 hover:text-gray-200 transition-colors">
                Feed
              </Link>
              <Link to="/admin" className="text-gray-400 hover:text-gray-200 transition-colors">
                Admin
              </Link>
            </nav>
          </div>
          {userId ? (
            <div className="flex items-center gap-3 text-sm">
              <span className="text-gray-400">
                <strong className="text-gray-200">{nickname}</strong>
              </span>
              <button
                onClick={handleLogout}
                className="text-gray-500 hover:text-gray-300 transition-colors"
              >
                Logout
              </button>
            </div>
          ) : (
            <form onSubmit={handleLogin} className="flex gap-2">
              <input
                type="text"
                value={nicknameInput}
                onChange={(e) => setNicknameInput(e.target.value)}
                placeholder="닉네임 입력..."
                className="bg-gray-900 border border-gray-700 rounded px-3 py-1 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-gray-500"
              />
              <button
                type="submit"
                className="bg-indigo-600 hover:bg-indigo-500 text-sm px-3 py-1 rounded transition-colors"
              >
                Join
              </button>
            </form>
          )}
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
