import type { CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import type { TagWithCount } from '../types'

export function TagBar({ tags, untagged, active, untaggedActive = false, variant = 'inline' }: {
  tags: TagWithCount[]
  untagged: number
  active: string | null
  untaggedActive?: boolean
  variant?: 'inline' | 'sidebar'
}) {
  // 没有讨论的标签不展示，避免空板块占位置
  const visible = tags.filter((t) => t.count > 0)

  return (
    <nav className={`tagbar ${variant}`}>
      <Link
        to="/?untagged=1"
        className={untaggedActive ? 'active' : ''}
        style={{ '--tag': '#999' } as CSSProperties}
      >
        无标签<span className="n">{untagged}</span>
      </Link>
      {visible.map((t) => (
        <Link
          key={t.id}
          to={`/?tag=${t.slug}`}
          className={t.slug === active ? 'active' : ''}
          style={{ '--tag': t.color ?? '#999' } as CSSProperties}
        >
          {t.name}<span className="n">{t.count}</span>
        </Link>
      ))}
    </nav>
  )
}
