import type { CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import type { TagWithCount } from '../types'
import { tagTone } from '../lib/tag'

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
        data-tone={tagTone('#999')}
        style={{ '--tag': '#999' } as CSSProperties}
      >
        {variant === 'sidebar'
          ? <span className="tag" style={{ '--tag': '#999' } as CSSProperties}>无标签</span>
          : '无标签'}
        <span className="n">{untagged}</span>
      </Link>
      {visible.map((t) => (
        <Link
          key={t.id}
          to={`/?tag=${t.slug}`}
          className={t.slug === active ? 'active' : ''}
          data-tone={tagTone(t.color)}
          style={{ '--tag': t.color ?? '#999' } as CSSProperties}
        >
          {variant === 'sidebar'
            ? <span className="tag" data-tone={tagTone(t.color)} style={{ '--tag': t.color ?? '#999' } as CSSProperties}>{t.name}</span>
            : t.name}
          <span className="n">{t.count}</span>
        </Link>
      ))}
    </nav>
  )
}
