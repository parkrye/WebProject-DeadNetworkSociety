import { useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from './shared/Layout'
import { FeedPage } from './pages/FeedPage'
import { PostDetailPage } from './pages/PostDetailPage'
import { userApi } from './domains/user/api'

function App() {
  const [userId, setUserId] = useState<string | null>(null)
  const [nickname, setNickname] = useState('')
  const [nicknameInput, setNicknameInput] = useState('')

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!nicknameInput.trim()) return
    try {
      const user = await userApi.create({ nickname: nicknameInput.trim() })
      setUserId(user.id)
      setNickname(user.nickname)
    } catch {
      alert('Nickname might be taken. Try another one.')
    }
  }

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950 text-gray-100">
        <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold">Dead Network Society</h1>
          {userId ? (
            <span className="text-sm text-gray-400">Logged in as <strong className="text-gray-200">{nickname}</strong></span>
          ) : (
            <form onSubmit={handleLogin} className="flex gap-2">
              <input
                type="text"
                value={nicknameInput}
                onChange={(e) => setNicknameInput(e.target.value)}
                placeholder="Enter nickname..."
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
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
