import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useDiscussion, useTimeline } from '../api/hooks'
import { PostCard } from '../components/PostCard'
import { datetime, displayName } from '../lib/format'

export function DiscussionPage() {
  const { id } = useParams()
  const discussionId = Number(id)
  const [page, setPage] = useState(1)
  const discussion = useDiscussion(discussionId)
  const timeline = useTimeline(discussionId, page)

  if (discussion.isLoading) return <p className="muted">加载中…</p>
  if (discussion.isError || !discussion.data) return <p>讨论不存在。<Link to="/">返回</Link></p>
  const d = discussion.data

  return (
    <>
      <h1>{d.title}</h1>
      <p className="muted">
        {displayName(d.author)} · {datetime(d.created_at)} · {timeline.data?.total ?? d.post_count} 帖
        {d.is_locked && ' · 已锁定'}
      </p>
      {d.tags.length > 0 && (
        <p className="post-tags">
          {d.tags.map((t) => (
            <span key={t.id} className="tag" style={{ '--tag': t.color ?? '#999' } as never}>
              <Link to={`/?tag=${t.slug}`}>{t.name}</Link>
            </span>
          ))}
        </p>
      )}

      {timeline.data?.items.map((item) =>
        item.type === 'event' && item.event ? (
          <p key={`e${item.id}`} className="event">{item.event.text}</p>
        ) : item.post ? (
          <PostCard
            key={`p${item.id}`}
            post={item.post}
            best={item.post.id === d.best_answer_post_id}
          />
        ) : null,
      )}

      <p className="pager">
        {page > 1 && <a href="#" onClick={(e) => { e.preventDefault(); setPage(page - 1) }}>← 上一页</a>}
        <span>{page} / {timeline.data?.pages ?? 1}</span>
        {page < (timeline.data?.pages ?? 1) && (
          <a href="#" onClick={(e) => { e.preventDefault(); setPage(page + 1) }}>下一页 →</a>
        )}
      </p>
    </>
  )
}
