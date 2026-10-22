import type { UserBrief } from '../types'

interface Props {
  user: UserBrief | null
  size?: number
}

export function Avatar({ user, size = 26 }: Props) {
  const name = user ? user.nickname || user.username : '匿'
  const path = user?.avatar_path
  const src = path
    ? path.startsWith('http')
      ? path
      : `/media/avatars/${encodeURIComponent(path)}`
    : null

  if (src) {
    return (
      <img
        className="avatar"
        src={src}
        alt={name}
        width={size}
        height={size}
        loading="lazy"
      />
    )
  }
  return (
    <span
      className="avatar avatar-fallback"
      style={{ width: size, height: size, fontSize: Math.round(size * 0.45) }}
    >
      {name.slice(0, 1).toUpperCase()}
    </span>
  )
}
