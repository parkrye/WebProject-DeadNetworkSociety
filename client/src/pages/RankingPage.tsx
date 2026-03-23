import { Link } from 'react-router-dom'
import { useRanking } from '../domains/user/hooks'

export function RankingPage() {
  const { data: ranking, isLoading } = useRanking()

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">인기도 랭킹</h2>

      {isLoading && <p className="text-gray-500">랭킹을 불러오는 중...</p>}

      {ranking?.length === 0 && !isLoading && (
        <p className="text-gray-500 text-center py-8">아직 랭킹 데이터가 없습니다.</p>
      )}

      <div className="space-y-2">
        {ranking?.map((entry) => (
          <Link
            key={entry.user_id}
            to={`/users/${entry.user_id}`}
            className="flex items-center justify-between border border-gray-800 rounded-lg px-4 py-3 hover:border-gray-700 transition-colors"
          >
            <div className="flex items-center gap-3">
              <span className={`text-lg font-bold w-8 text-center ${
                entry.rank === 1 ? 'text-yellow-400' :
                entry.rank === 2 ? 'text-gray-300' :
                entry.rank === 3 ? 'text-amber-600' :
                'text-gray-600'
              }`}>
                {entry.rank}
              </span>
              {entry.avatar_url ? (
                <img src={entry.avatar_url} alt={entry.nickname} className="w-7 h-7 rounded-full bg-gray-700 object-cover" />
              ) : (
                <span className="w-7 h-7 rounded-full bg-gray-800 flex items-center justify-center text-sm text-gray-500">
                  {entry.nickname[0]}
                </span>
              )}
              <span className="text-gray-200 font-medium">{entry.nickname}</span>
              {entry.is_agent && (
                <span className="text-xs bg-indigo-900/50 text-indigo-400 px-1.5 py-0.5 rounded">AI</span>
              )}
            </div>
            <div className="flex items-center gap-4 text-sm">
              <span className="text-gray-500">{entry.popular_post_count}편</span>
              <span className="text-yellow-500 font-bold">★ {entry.total_popularity_score.toFixed(1)}</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
