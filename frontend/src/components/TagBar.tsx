import type { CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import type { TagWithCount } from '../types'
import { tagTone } from '../lib/tag'

export function TagBar({ tags, untagged, total, active, untaggedActive = false,
                         showAll = false, allActive = false, variant = 'inline' }: {
  tags: TagWithCount[]
  untagged: number
  total?: number
  active: string | null
  untaggedActive?: boolean
  /** 站点配了默认板块时才显示「全部」，否则首页本来就展示全部 */
  showAll?: boolean
  allActive?: boolean
  variant?: 'inline' | 'sidebar'
}) {
  // 没有讨论的标签不展示，避免空板块占位置
  const visible = tags.filter((t) => t.count > 0)

  return (
    <nav className={`tagbar ${variant}`}>
      {showAll && (
        <Link
          to="/?all=1"
          className={allActive ? 'active' : ''}
          data-tone={tagTone(null)}
        >
          {variant === 'sidebar'
            ? <span className="tag">全部</span>
            : '全部'}
          {total !== undefined && <span className="n">{total}</span>}
        </Link>
      )}
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
