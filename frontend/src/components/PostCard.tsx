import { useEffect, useRef, useState } from 'react'
import type { Post } from '../types'
import { renderMath } from '../lib/math'
import { datetime, displayName } from '../lib/format'
import { MarkdownEditor } from './MarkdownEditor'
import { Avatar } from './Avatar'

interface Props {
  post: Post
  best: boolean
  canEdit: boolean
  canModerate: boolean
  quoteOn: boolean
  onQuote: (post: Post) => void
  onEdit: (id: number, body: string) => void
  onBest: (id: number) => void
  saving: boolean
}

export function PostCard({
  post, best, canEdit, canModerate, quoteOn, onQuote, onEdit, onBest, saving,
}: Props) {
  const body = useRef<HTMLDivElement>(null)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')

  useEffect(() => {
    if (!editing) renderMath(body.current)
  }, [post.body_html, editing])

  return (
    <div className={best ? 'post best-answer' : 'post'} id={`p${post.id}`}>
      <div className="post-head">
        <span className="floor">#{post.number}</span>
        <span className="avatar-slot"><Avatar user={post.author} /></span>
        <span className="who">
          <span className="author">{displayName(post.author)}</span>
          <span className="time">{datetime(post.created_at)}</span>
        </span>
        <span className="actions">
          {best && <span className="best">最佳回复</span>}
          {quoteOn && (
            <button type="button" title="引用这一楼" onClick={() => onQuote(post)}>引用</button>
          )}
          {canEdit && !post.is_legacy && !editing && (
            <button type="button" title="编辑这一楼"
                    onClick={() => { setDraft(post.body_md ?? ''); setEditing(true) }}>编辑</button>
          )}
          {canModerate && !best && (
            <button type="button" title="设为最佳回复" onClick={() => onBest(post.id)}>最佳</button>
          )}
        </span>
      </div>

      {editing ? (
        <div className="post-body">
          <p className="muted">旧帖子没有 Markdown 原文，编辑会以新内容覆盖。</p>
          <MarkdownEditor value={draft} onChange={setDraft} rows={8} />
          <p>
            <button type="button" disabled={saving || !draft.trim()}
                    onClick={() => { onEdit(post.id, draft); setEditing(false) }}>
              保存
            </button>{' '}
            <button type="button" onClick={() => setEditing(false)}>取消</button>
          </p>
        </div>
      ) : (
        <div className="post-body" ref={body} dangerouslySetInnerHTML={{ __html: post.body_html }} />
      )}
      {post.edited_at && <p className="edited">编辑于 {datetime(post.edited_at)}</p>}
    </div>
  )
}
