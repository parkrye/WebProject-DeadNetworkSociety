import { Link } from 'react-router-dom'

const ANON_NICKNAME = '이름없는오가닉유저'

interface AuthorLinkProps {
  authorId: string
  nickname: string
  avatarUrl?: string
  size?: 'sm' | 'md'
}

export function AuthorLink({ authorId, nickname, avatarUrl, size = 'sm' }: AuthorLinkProps) {
  const isAnon = nickname === ANON_NICKNAME
  const dim = size === 'sm' ? 'w-5 h-5 text-xs' : 'w-7 h-7 text-sm'

  const avatar = avatarUrl ? (
    <img src={avatarUrl} alt={nickname} className={`${dim} rounded-full bg-gray-700 object-cover`} />
  ) : (
    <span className={`${dim} rounded-full bg-gray-800 flex items-center justify-center text-gray-500`}>
      {nickname[0]}
    </span>
  )

  if (isAnon) {
    return (
      <span className="flex items-center gap-2 text-gray-500">
        {avatar}
        <span>{nickname}</span>
      </span>
    )
  }

  return (
    <Link
      to={`/users/${authorId}`}
      onClick={(e) => e.stopPropagation()}
      className="flex items-center gap-2 hover:text-gray-200 transition-colors"
    >
      {avatar}
      <span className="text-gray-400 font-medium">{nickname}</span>
    </Link>
  )
}
