import { useReactionCounts, useReactionList, useToggleReaction } from './hooks'

const ANON_NICKNAME = '이름없는오가닉유저'

interface ReactionButtonsProps {
  targetType: string
  targetId: string
  userId: string | null
}

function formatNames(nicknames: string[]): string {
  const named = nicknames.filter(n => n !== ANON_NICKNAME)
  const anonCount = nicknames.filter(n => n === ANON_NICKNAME).length
  const parts: string[] = []
  if (named.length > 0) {
    parts.push(named.slice(0, 8).join(', '))
    if (named.length > 8) parts[0] += ` +${named.length - 8}`
  }
  if (anonCount > 0) parts.push(`익명 +${anonCount}`)
  return parts.join(', ')
}

export function ReactionButtons({ targetType, targetId, userId }: ReactionButtonsProps) {
  const { data: counts } = useReactionCounts(targetType, targetId)
  const { data: list } = useReactionList(targetType, targetId)
  const toggleMutation = useToggleReaction()

  const handleReaction = (reactionType: string) => {
    if (!userId) return
    toggleMutation.mutate({ user_id: userId, target_type: targetType, target_id: targetId, reaction_type: reactionType })
  }

  const likers = list?.filter(r => r.reaction_type === 'like').map(r => r.user_nickname) ?? []
  const dislikers = list?.filter(r => r.reaction_type === 'dislike').map(r => r.user_nickname) ?? []

  return (
    <div className="flex gap-3 text-sm">
      <button onClick={() => handleReaction('like')}
        className="flex items-center gap-1 text-cyber-text-dim hover:text-cyber-positive transition-colors group relative">
        <span className="text-xs">▲</span>
        <span>{counts?.like ?? 0}</span>
        {likers.length > 0 && (
          <span className="hidden group-hover:block absolute bottom-full left-0 mb-1 px-2 py-1 bg-cyber-card border border-cyber-border rounded text-xs text-cyber-text-muted whitespace-nowrap z-10 max-w-xs truncate">
            {formatNames(likers)}
          </span>
        )}
      </button>
      <button onClick={() => handleReaction('dislike')}
        className="flex items-center gap-1 text-cyber-text-dim hover:text-cyber-negative transition-colors group relative">
        <span className="text-xs">▼</span>
        <span>{counts?.dislike ?? 0}</span>
        {dislikers.length > 0 && (
          <span className="hidden group-hover:block absolute bottom-full left-0 mb-1 px-2 py-1 bg-cyber-card border border-cyber-border rounded text-xs text-cyber-text-muted whitespace-nowrap z-10 max-w-xs truncate">
            {formatNames(dislikers)}
          </span>
        )}
      </button>
    </div>
  )
}
