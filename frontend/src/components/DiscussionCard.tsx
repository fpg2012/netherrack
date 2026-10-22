import type { CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import type { DiscussionBrief } from '../types'
import { date } from '../lib/format'

export function DiscussionCard({ d }: { d: DiscussionBrief }) {
  return (
    <div className="card">
      <Link className="card-title" to={`/d/${d.id}`}>{d.title}</Link>
      <div className="card-meta">{date(d.last_posted_at)} · {d.post_count} 回复</div>
      {d.tags.length > 0 && (
        <div className="card-tags">
          {d.tags.map((t) => (
            <span key={t.id} className="tag" style={{ '--tag': t.color ?? '#999' } as CSSProperties}>
              {t.name}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
