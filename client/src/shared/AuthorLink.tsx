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
  const dim = size === 'sm' ? 'w-5 h-5 text-[10px]' : 'w-7 h-7 text-xs'

  const avatar = avatarUrl ? (
    <img src={avatarUrl} alt={nickname} className={`${dim} rounded-full bg-cyber-card object-cover ring-1 ring-cyber-border`} />
  ) : (
    <span className={`${dim} rounded-full bg-cyber-card flex items-center justify-center text-cyber-text-dim ring-1 ring-cyber-border`}>
      {nickname[0]}
    </span>
  )

  if (isAnon) {
    return (
      <span className="flex items-center gap-1.5 text-cyber-text-dim">
        {avatar}
        <span>{nickname}</span>
      </span>
    )
  }

  return (
    <Link
      to={`/users/${authorId}`}
      onClick={(e) => e.stopPropagation()}
      className="flex items-center gap-1.5 hover:text-cyber-accent transition-colors"
    >
      {avatar}
      <span className="text-cyber-text-muted font-medium">{nickname}</span>
    </Link>
  )
}
