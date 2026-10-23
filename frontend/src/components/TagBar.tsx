import type { CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import type { TagWithCount } from '../types'

export function TagBar({ tags, total, active }: {
  tags: TagWithCount[]
  total: number
  active: string | null
}) {
  return (
    <nav className="tagbar">
      <Link to="/" className={active ? '' : 'active'}>全部<span className="n">{total}</span></Link>
      {tags.map((t) => (
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
