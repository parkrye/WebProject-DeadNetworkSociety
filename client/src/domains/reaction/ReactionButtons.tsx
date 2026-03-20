import { useReactionCounts, useToggleReaction } from './hooks'

interface ReactionButtonsProps {
  targetType: string
  targetId: string
  userId: string | null
}

export function ReactionButtons({ targetType, targetId, userId }: ReactionButtonsProps) {
  const { data: counts } = useReactionCounts(targetType, targetId)
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

  return (
    <div className="flex gap-3 text-sm">
      <button
        onClick={() => handleReaction('like')}
        className="flex items-center gap-1 text-gray-400 hover:text-green-400 transition-colors"
        disabled={!userId}
      >
        <span>+</span>
        <span>{counts?.like ?? 0}</span>
      </button>
      <button
        onClick={() => handleReaction('dislike')}
        className="flex items-center gap-1 text-gray-400 hover:text-red-400 transition-colors"
        disabled={!userId}
      >
        <span>-</span>
        <span>{counts?.dislike ?? 0}</span>
      </button>
    </div>
  )
}
