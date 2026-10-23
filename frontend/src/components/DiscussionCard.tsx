import type { CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import type { DiscussionBrief } from '../types'
import { date } from '../lib/format'

export function DiscussionCard({ d }: { d: DiscussionBrief }) {
  // 色相按 id 稳定散开；深浅仍按回复数变化（对数压缩，避免热帖一下子变黑）
  const hue = (d.id * 137.508) % 360
  const replies = Math.max(0, d.post_count - 1)
  const heat = Math.min(1, Math.log1p(replies) / Math.log1p(60))
  return (
    <div
      className="card"
      style={{ '--card-hue': hue.toFixed(1), '--heat': heat.toFixed(3) } as CSSProperties}
    >
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
