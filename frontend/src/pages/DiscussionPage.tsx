import { useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  useCollapsePost, useDiscussion, useEditDiscussion, useEditPost, useMe, useMentionable,
  useMeta, useReply, useTags, useTimeline,
} from '../api/hooks'
import { ApiError } from '../api/client'
import { PostCard } from '../components/PostCard'
import { Dropdown } from '../components/Dropdown'
import type { MenuItem } from '../components/Dropdown'
import { MarkdownEditor } from '../components/MarkdownEditor'
import { Sidebar } from '../components/Sidebar'
import { NotFoundPage } from './NotFoundPage'
import { datetime, displayName } from '../lib/format'
import { tagTone } from '../lib/tag'
import { useDraft } from '../lib/draft'
import type { Post } from '../types'

export function DiscussionPage() {
  const { id } = useParams()
  const discussionId = Number(id)
  const [page, setPage] = useState(1)
  const discussion = useDiscussion(discussionId)
  const timeline = useTimeline(discussionId, page)
  const me = useMe()
  const allTags = useTags()
  const meta = useMeta()

  const reply = useReply(discussionId)
  const editPost = useEditPost(discussionId)
  const editDiscussion = useEditDiscussion(discussionId)
  const collapsePost = useCollapsePost(discussionId)
  const mentionable = useMentionable(discussionId)

  const [draft, setDraft, clearDraft] = useDraft(`draft:reply:${discussionId}`, '')
  const [quote, setQuote] = useState<Post | null>(null)
  const [replyTo, setReplyTo] = useState<Post | null>(null)
  const [tagEditor, setTagEditor] = useState(false)
  const [titleEditor, setTitleEditor] = useState(false)
  const [titleDraft, setTitleDraft] = useState('')
  const [picked, setPicked] = useState<string[]>([])
  const replyBox = useRef<HTMLTextAreaElement>(null)

  if (discussion.isLoading) return <p className="muted">加载中…</p>
  // 私密讨论对游客按不存在处理（后端同样返回 404），不暴露它是否存在
  const notFound = (
    <div className="thread-layout">
      <div className="thread-main"><NotFoundPage /></div>
      <aside className="sidebar">
        <Sidebar tags={allTags.data ?? []} meta={meta.data} />
      </aside>
    </div>
  )
  if (discussion.isError) {
    if (discussion.error instanceof ApiError && discussion.error.status === 404) return notFound
    return <p className="muted">加载失败：{discussion.error.message}</p>
  }
  if (!discussion.data) return notFound
  const d = discussion.data
  const isAdmin = me.data?.is_admin ?? false
  const isAuthor = me.data?.id === d.author?.id
  const canReply = !!me.data && (!d.is_locked || isAdmin)

  const saveTitle = () => {
    const title = titleDraft.trim()
    if (title.length < 2 || title === d.title) return
    editDiscussion.mutate({ title }, { onSuccess: () => setTitleEditor(false) })
  }

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
    <div className="thread-layout">
      <div className="thread-main">
      {titleEditor ? (
        <div className="title-editor">
          <input
            className="title-input"
            value={titleDraft}
            maxLength={200}
            autoFocus
            onChange={(e) => setTitleDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') saveTitle()
              if (e.key === 'Escape') setTitleEditor(false)
            }}
          />
          <button
            className="btn"
            disabled={editDiscussion.isPending || titleDraft.trim().length < 2
              || titleDraft.trim() === d.title}
            onClick={saveTitle}
          >
            保存
          </button>
          <button className="btn" onClick={() => setTitleEditor(false)}>取消</button>
        </div>
      ) : (
        <h1>{d.title}</h1>
      )}
      <div className="discussion-meta">
        <p className="muted">
          {displayName(d.author)} · {datetime(d.created_at)} · {timeline.data?.total ?? d.post_count} 帖
          {d.is_sticky && ' · 已置顶'}
          {d.is_locked && ' · 已锁定'}
          {d.is_collapsed && ' · 已折叠'}
        </p>
        {(isAdmin || isAuthor) && (
          <Dropdown
            label={isAdmin ? '管理' : '操作'}
            items={[
              {
                label: '改标题…',
                onSelect: () => {
                  setTitleDraft(d.title)
                  setTitleEditor(true)
                },
              },
              {
                label: '改标签…',
                onSelect: () => {
                  setPicked(d.tags.map((t) => t.slug))
                  setTagEditor(true)
                },
              },
              { divider: true },
              {
                label: d.is_public ? '转为私密' : '设为公开',
                // 折叠的讨论一定不公开，这个选项直接禁用
                disabled: editDiscussion.isPending || d.is_collapsed,
                onSelect: () => editDiscussion.mutate({ is_public: !d.is_public }),
              },
              ...(isAdmin
                ? ([
                    { divider: true },
                    {
                      label: d.is_sticky ? '取消置顶' : '置顶',
                      disabled: editDiscussion.isPending,
                      onSelect: () => editDiscussion.mutate({ is_sticky: !d.is_sticky }),
                    },
                    {
                      label: d.is_locked ? '解锁' : '锁定',
                      disabled: editDiscussion.isPending,
                      onSelect: () => editDiscussion.mutate({ is_locked: !d.is_locked }),
                    },
                    {
                      label: d.is_collapsed ? '解除折叠' : '折叠讨论',
                      disabled: editDiscussion.isPending,
                      onSelect: () => editDiscussion.mutate({ is_collapsed: !d.is_collapsed }),
                    },
                  ] satisfies MenuItem[])
                : []),
            ]}
          />
        )}
      </div>

      <div className="post-tags">
        {d.tags.map((t) => (
          <span key={t.id} className="tag" data-tone={tagTone(t.color)} style={{ '--tag': t.color ?? '#999' } as never}>
            <Link to={`/?tag=${t.slug}`}>{t.name}</Link>
          </span>
        ))}
      </div>

      {tagEditor && (
        <div className="tag-editor">
          <div className="tag-options">
            {allTags.data?.map((t) => {
              const on = picked.includes(t.slug)
              return (
                <label key={t.id} className={on ? 'on' : ''}>
                  <input
                    type="checkbox"
                    checked={on}
                    disabled={!on && picked.length >= 5}
                    onChange={(e) => setPicked(e.target.checked
                      ? [...picked, t.slug]
                      : picked.filter((s) => s !== t.slug))}
                  />
                  <span className="tag" data-tone={tagTone(t.color)} style={{ '--tag': t.color ?? '#999' } as never}>
                    {t.name}
                  </span>
                </label>
              )
            })}
          </div>
          <div className="tag-editor-actions">
            <span className="hint">{picked.length}/5</span>
            <button
              type="button"
              disabled={editDiscussion.isPending}
              onClick={() => editDiscussion.mutate(
                { tags: picked },
                { onSuccess: () => setTagEditor(false) },
              )}
            >
              {editDiscussion.isPending ? '保存中…' : '保存'}
            </button>
            <button type="button" onClick={() => setTagEditor(false)}>取消</button>
            {editDiscussion.isError && <span className="event"> 保存失败</span>}
          </div>
        </div>
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
            onCollapse={(postId, collapsed) =>
              collapsePost.mutate({ id: postId, is_collapsed: collapsed })}
            onReplyTo={(post) => { setReplyTo(post); replyBox.current?.focus() }}
            mentionable={mentionable.data}
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
          {replyTo && (
            <p className="muted">
              正在回复 #{replyTo.number} {displayName(replyTo.author)}{' '}
              <button type="button" className="linklike" onClick={() => setReplyTo(null)}>
                取消
              </button>
            </p>
          )}
          <MarkdownEditor value={draft} onChange={setDraft} rows={8}
                          mentionable={mentionable.data}
                          placeholder="支持 Markdown，$公式$ 会被 KaTeX 渲染" />
          <p>
            <button
              type="button"
              disabled={reply.isPending || !draft.trim()}
              onClick={() => {
                reply.mutate(
                  {
                    body_md: draft,
                    quote_post_id: quote?.id ?? null,
                    reply_to_post_id: replyTo?.id ?? null,
                  },
                  {
                    onSuccess: () => {
                      clearDraft()
                      setQuote(null)
                      setReplyTo(null)
                    },
                  },
                )
              }}
            >
              {reply.isPending ? '提交中…' : '提交'}
            </button>
            {reply.isError && <span className="event"> 提交失败</span>}
          </p>
        </div>
      )}
      </div>

      <aside className="sidebar">
        <Sidebar tags={allTags.data ?? []} meta={meta.data} />
      </aside>
    </div>
  )
}
