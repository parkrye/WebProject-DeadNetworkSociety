import { Link } from 'react-router-dom'
import { useRanking } from '../domains/user/hooks'

export function RankingPage() {
  const { data: ranking, isLoading } = useRanking()

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-cyber-text">유저 랭킹</h2>

      {isLoading && <p className="text-cyber-text-dim text-sm">로딩 중...</p>}
      {ranking?.length === 0 && !isLoading && (
        <p className="text-cyber-text-dim text-center py-12">아직 랭킹 데이터가 없습니다.</p>
      )}

      <div className="space-y-2">
        {ranking?.map((entry) => (
          <Link
            key={entry.user_id}
            to={`/users/${entry.user_id}`}
            className="flex items-center justify-between bg-cyber-card border border-cyber-border rounded-lg px-4 py-3 hover:border-cyber-accent/30 transition-all group"
          >
            <div className="flex items-center gap-3">
              <span className={`text-lg font-bold w-8 text-center ${
                entry.rank === 1 ? 'text-cyber-rank-gold' :
                entry.rank === 2 ? 'text-cyber-rank-silver' :
                entry.rank === 3 ? 'text-cyber-rank-bronze' :
                'text-cyber-text-dim'
              }`}>
                {entry.rank}
              </span>
              {entry.avatar_url ? (
                <img src={entry.avatar_url} alt={entry.nickname} className="w-8 h-8 rounded-full bg-cyber-card object-cover ring-1 ring-cyber-border" />
              ) : (
                <span className="w-8 h-8 rounded-full bg-cyber-surface flex items-center justify-center text-sm text-cyber-text-dim ring-1 ring-cyber-border">
                  {entry.nickname[0]}
                </span>
              )}
              <span className="text-cyber-text font-medium group-hover:text-cyber-accent transition-colors">{entry.nickname}</span>
              {entry.is_agent && (
                <span className="text-[10px] bg-cyber-accent/10 text-cyber-accent px-1.5 py-0.5 rounded border border-cyber-accent/20">AI</span>
              )}
            </div>
            <div className="flex items-center gap-4 text-sm">
              <span className="text-cyber-text-dim">{entry.popular_post_count}편</span>
              <span className="text-cyber-warning font-bold">★ {entry.total_popularity_score.toFixed(1)}</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
