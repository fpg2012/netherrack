import { useEffect, useRef } from 'react'
import type { Post } from '../types'
import { renderMath } from '../lib/math'
import { datetime, displayName } from '../lib/format'

export function PostCard({ post, best }: { post: Post; best: boolean }) {
  const body = useRef<HTMLDivElement>(null)

  useEffect(() => {
    renderMath(body.current)
  }, [post.body_html])

  return (
    <div className={best ? 'post best-answer' : 'post'} id={`p${post.id}`}>
      {best && <span className="best">最佳回复</span>}
      <div className="post-head">
        <span className="floor">#{post.number}</span>
        <span className="who">
          <span className="author">{displayName(post.author)}</span>
          <span className="time">{datetime(post.created_at)}</span>
        </span>
      </div>
      <div className="post-body" ref={body} dangerouslySetInnerHTML={{ __html: post.body_html }} />
      {post.edited_at && <p className="edited">编辑于 {datetime(post.edited_at)}</p>}
    </div>
  )
}
