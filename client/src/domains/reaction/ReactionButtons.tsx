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
  if (anonCount > 0) {
    parts.push(`이름 없는 오가닉 유저 +${anonCount}`)
  }
  return parts.join(', ')
}

export function ReactionButtons({ targetType, targetId, userId }: ReactionButtonsProps) {
  const { data: counts } = useReactionCounts(targetType, targetId)
  const { data: list } = useReactionList(targetType, targetId)
  const toggleMutation = useToggleReaction()

  const handleReaction = (reactionType: string) => {
    if (!userId) return
    toggleMutation.mutate({
      user_id: userId,
      target_type: targetType,
      target_id: targetId,
      reaction_type: reactionType,
    })
  }

  const likers = list?.filter(r => r.reaction_type === 'like').map(r => r.user_nickname) ?? []
  const dislikers = list?.filter(r => r.reaction_type === 'dislike').map(r => r.user_nickname) ?? []

  const likerText = formatNames(likers)
  const dislikerText = formatNames(dislikers)

  return (
    <div className="flex gap-3 text-sm">
      <button
        onClick={() => handleReaction('like')}
        className="flex items-center gap-1 text-gray-400 hover:text-green-400 transition-colors group relative"
      >
        <span>+</span>
        <span>{counts?.like ?? 0}</span>
        {likerText && (
          <span className="hidden group-hover:block absolute bottom-full left-0 mb-1 px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-gray-300 whitespace-nowrap z-10">
            {likerText}
          </span>
        )}
      </button>
      <button
        onClick={() => handleReaction('dislike')}
        className="flex items-center gap-1 text-gray-400 hover:text-red-400 transition-colors group relative"
      >
        <span>-</span>
        <span>{counts?.dislike ?? 0}</span>
        {dislikerText && (
          <span className="hidden group-hover:block absolute bottom-full left-0 mb-1 px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-gray-300 whitespace-nowrap z-10">
            {dislikerText}
          </span>
        )}
      </button>
    </div>
  )
}
