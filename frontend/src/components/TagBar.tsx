import type { CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import type { TagWithCount } from '../types'

export function TagBar({ tags, total, active, variant = 'inline' }: {
  tags: TagWithCount[]
  total: number
  active: string | null
  variant?: 'inline' | 'sidebar'
}) {
  return (
    <nav className={`tagbar ${variant}`}>
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
