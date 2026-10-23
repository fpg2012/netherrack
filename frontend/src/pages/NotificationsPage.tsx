import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  useBroadcast, useMarkRead, useMe, useNotifications, useReadAll,
} from '../api/hooks'
import { datetime, displayName } from '../lib/format'

const KIND_TEXT: Record<string, string> = {
  reply: '回复了你的讨论',
  quote: '引用了你的回复',
  best_answer: '把你的回复设为最佳',
  mention: '在帖子里提到了你',
}

export function NotificationsPage() {
  const me = useMe()
  const [page, setPage] = useState(1)
  const list = useNotifications(page)
  const readAll = useReadAll()
  const markRead = useMarkRead()
  const broadcast = useBroadcast()
  // 顶栏菜单「发送系统通知」跳过来时直接把表单展开
  const [params] = useSearchParams()
  const [sendOpen, setSendOpen] = useState(params.get('send') === '1')
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')

  if (!me.data) return <p className="muted"><Link to="/login">登录</Link> 后查看通知。</p>

  return (
    <>
      <h1>通知</h1>
      <p className="muted">
        共 {list.data?.total ?? 0} 条
        {list.data?.items.some((n) => !n.read) && (
          <>
            {' · '}
            <button type="button" className="linklike" disabled={readAll.isPending}
                    onClick={() => readAll.mutate()}>
              全部标为已读
            </button>
          </>
        )}
        {me.data.is_admin && (
          <>
            {' · '}
            <button type="button" className="linklike"
                    onClick={() => setSendOpen((v) => !v)}>
              {sendOpen ? '收起' : '发送系统通知'}
            </button>
          </>
        )}
      </p>

      {sendOpen && me.data.is_admin && (
        <div className="notice-form">
          <label>
            <span>标题</span>
            <input className="inline" value={title} maxLength={120}
                   onChange={(e) => setTitle(e.target.value)} />
          </label>
          <label>
            <span>正文</span>
            <textarea className="inline" rows={4} value={body} maxLength={5000}
                      onChange={(e) => setBody(e.target.value)} />
          </label>
          <div className="settings-actions">
            <button type="button" className="button"
                    disabled={broadcast.isPending || !title.trim() || !body.trim()}
                    onClick={() => broadcast.mutate({ title, body }, {
                      onSuccess: () => { setTitle(''); setBody(''); setSendOpen(false) },
                    })}>
              {broadcast.isPending ? '发送中…' : '发送给所有用户'}
            </button>
            {broadcast.isSuccess && (
              <span className="msg ok">已发送给 {broadcast.data.sent} 人</span>
            )}
            {broadcast.isError && <span className="msg err">{broadcast.error.message}</span>}
          </div>
        </div>
      )}

      <ul className="notifications">
        {list.data?.items.map((n) => (
          <li key={n.id} className={n.read ? '' : 'unread'}>
            {n.kind === 'system' ? (
              <>
                <div className="notif-title">{n.title}</div>
                <p className="notif-body">{n.body}</p>
                <div className="muted small">
                  系统通知{displayName(n.actor) ? ` · ${displayName(n.actor)}` : ''} · {datetime(n.created_at)}
                </div>
              </>
            ) : (
              <>
                <Link to={`/d/${n.discussion_id}#p${n.post_id}`} className="notif-title"
                      onClick={() => { if (!n.read) markRead.mutate(n.id) }}>
                  {n.discussion_title}
                </Link>
                <div className="muted small">
                  {displayName(n.actor)} {KIND_TEXT[n.kind] ?? n.kind}
                  {n.post_number ? ` · #${n.post_number}` : ''} · {datetime(n.created_at)}
                </div>
              </>
            )}
          </li>
        ))}
      </ul>
      {list.data?.total === 0 && <p className="muted">还没有通知。</p>}

      <p className="pager">
        {page > 1 && <a href="#" onClick={(e) => { e.preventDefault(); setPage(page - 1) }}>← 上一页</a>}
        <span>{page} / {list.data?.pages ?? 1}</span>
        {page < (list.data?.pages ?? 1) && (
          <a href="#" onClick={(e) => { e.preventDefault(); setPage(page + 1) }}>下一页 →</a>
        )}
      </p>
    </>
  )
}
