import { useReactionCounts, useReactionList, useToggleReaction } from './hooks'

interface ReactionButtonsProps {
  targetType: string
  targetId: string
  userId: string | null
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

  return (
    <div className="flex gap-3 text-sm">
      <button
        onClick={() => handleReaction('like')}
        className="flex items-center gap-1 text-gray-400 hover:text-green-400 transition-colors group relative"
        disabled={!userId}
        title={likers.length > 0 ? likers.join(', ') : undefined}
      >
        <span>+</span>
        <span>{counts?.like ?? 0}</span>
        {likers.length > 0 && (
          <span className="hidden group-hover:block absolute bottom-full left-0 mb-1 px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-gray-300 whitespace-nowrap z-10">
            {likers.slice(0, 10).join(', ')}{likers.length > 10 ? ` +${likers.length - 10}` : ''}
          </span>
        )}
      </button>
      <button
        onClick={() => handleReaction('dislike')}
        className="flex items-center gap-1 text-gray-400 hover:text-red-400 transition-colors group relative"
        disabled={!userId}
        title={dislikers.length > 0 ? dislikers.join(', ') : undefined}
      >
        <span>-</span>
        <span>{counts?.dislike ?? 0}</span>
        {dislikers.length > 0 && (
          <span className="hidden group-hover:block absolute bottom-full left-0 mb-1 px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-gray-300 whitespace-nowrap z-10">
            {dislikers.slice(0, 10).join(', ')}{dislikers.length > 10 ? ` +${dislikers.length - 10}` : ''}
          </span>
        )}
      </button>
    </div>
  )
}
