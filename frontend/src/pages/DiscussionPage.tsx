import { useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useDiscussion, useEditDiscussion, useEditPost, useMe, useReply, useTimeline } from '../api/hooks'
import { PostCard } from '../components/PostCard'
import { MarkdownEditor } from '../components/MarkdownEditor'
import { datetime, displayName } from '../lib/format'
import type { Post } from '../types'

export function DiscussionPage() {
  const { id } = useParams()
  const discussionId = Number(id)
  const [page, setPage] = useState(1)
  const discussion = useDiscussion(discussionId)
  const timeline = useTimeline(discussionId, page)
  const me = useMe()

  const reply = useReply(discussionId)
  const editPost = useEditPost(discussionId)
  const editDiscussion = useEditDiscussion(discussionId)

  const [draft, setDraft] = useState('')
  const [quote, setQuote] = useState<Post | null>(null)
  const [tagInput, setTagInput] = useState<string | null>(null)
  const replyBox = useRef<HTMLTextAreaElement>(null)

  if (discussion.isLoading) return <p className="muted">加载中…</p>
  if (discussion.isError || !discussion.data) return <p>讨论不存在。<Link to="/">返回</Link></p>
  const d = discussion.data
  const isAdmin = me.data?.is_admin ?? false
  const isAuthor = me.data?.id === d.author?.id
  const canReply = !!me.data && (!d.is_locked || isAdmin)

  const quoteText = (post: Post) => {
    const text = (post.body_html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()).slice(0, 200)
    return `> **${displayName(post.author)}** 在 #${post.number} 写道：\n> ${text}\n\n`
  }

  const onQuote = (post: Post) => {
    setQuote(post)
    if (!draft.includes(`#${post.number} 写道`)) setDraft(quoteText(post) + draft)
    replyBox.current?.focus()
  }

  return (
    <>
      <h1>{d.title}</h1>
      <p className="muted">
        {displayName(d.author)} · {datetime(d.created_at)} · {timeline.data?.total ?? d.post_count} 帖
        {d.is_locked && ' · 已锁定'}
      </p>

      <p className="post-tags">
        {d.tags.map((t) => (
          <span key={t.id} className="tag" style={{ '--tag': t.color ?? '#999' } as never}>
            <Link to={`/?tag=${t.slug}`}>{t.name}</Link>
          </span>
        ))}
        {(isAdmin || isAuthor) && (
          <button type="button" className="linklike"
                  onClick={() => setTagInput(tagInput === null ? d.tags.map((t) => t.slug).join(', ') : null)}>
            改标签
          </button>
        )}
      </p>

      {tagInput !== null && (
        <p>
          <input className="inline" value={tagInput} onChange={(e) => setTagInput(e.target.value)}
                 placeholder="逗号分隔的标签 slug" />
          <button type="button" disabled={editDiscussion.isPending}
                  onClick={() => {
                    editDiscussion.mutate({
                      tags: tagInput.split(',').map((s) => s.trim()).filter(Boolean),
                    })
                    setTagInput(null)
                  }}>保存</button>
          {editDiscussion.isError && <span className="event"> 保存失败</span>}
        </p>
      )}

      {isAdmin && (
        <p className="adminbar">
          <button type="button" disabled={editDiscussion.isPending}
                  onClick={() => editDiscussion.mutate({ is_sticky: !d.is_sticky })}>
            {d.is_sticky ? '取消置顶' : '置顶'}
          </button>
          <button type="button" disabled={editDiscussion.isPending}
                  onClick={() => editDiscussion.mutate({ is_locked: !d.is_locked })}>
            {d.is_locked ? '解锁' : '锁定'}
          </button>
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
            canEdit={!!me.data && (me.data.id === item.post.author?.id || isAdmin)}
            canModerate={isAdmin}
            quoteOn={!!me.data}
            onQuote={onQuote}
            onEdit={(postId, body) => editPost.mutate({ id: postId, body_md: body })}
            onBest={(postId) => editDiscussion.mutate({ best_answer_post_id: postId })}
            saving={editPost.isPending}
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

      <hr />
      {!me.data ? (
        <p className="muted"><Link to="/login">登录</Link> 后可以回复。</p>
      ) : !canReply ? (
        <p className="muted">讨论已锁定，只有管理员可以回复。</p>
      ) : (
        <div className="reply">
          <h2 className="small">回复</h2>
          {quote && (
            <p className="muted">
              正在引用 #{quote.number} {displayName(quote.author)}{' '}
              <button type="button" className="linklike" onClick={() => setQuote(null)}>
                取消
              </button>
            </p>
          )}
          <MarkdownEditor value={draft} onChange={setDraft} rows={8} placeholder="支持 Markdown，$公式$ 会被 KaTeX 渲染" />
          <p>
            <button
              type="button"
              disabled={reply.isPending || !draft.trim()}
              onClick={() => {
                reply.mutate(
                  { body_md: draft, quote_post_id: quote?.id ?? null },
                  { onSuccess: () => { setDraft(''); setQuote(null) } },
                )
              }}
            >
              {reply.isPending ? '提交中…' : '提交'}
            </button>
            {reply.isError && <span className="event"> 提交失败</span>}
          </p>
        </div>
      )}
    </>
  )
}
