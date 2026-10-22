import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMe, useNotifications, useReadAll } from '../api/hooks'
import { datetime, displayName } from '../lib/format'

const KIND_TEXT: Record<string, string> = {
  reply: '回复了你的讨论',
  quote: '引用了你的回复',
  best_answer: '把你的回复设为最佳',
}

export function NotificationsPage() {
  const me = useMe()
  const [page, setPage] = useState(1)
  const list = useNotifications(page)
  const readAll = useReadAll()

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
      </p>

      <ul className="notifications">
        {list.data?.items.map((n) => (
          <li key={n.id} className={n.read ? '' : 'unread'}>
            <Link to={`/d/${n.discussion_id}#p${n.post_id}`} className="notif-title">
              {n.discussion_title}
            </Link>
            <div className="muted small">
              {displayName(n.actor)} {KIND_TEXT[n.kind] ?? n.kind}
              {n.post_number ? ` · #${n.post_number}` : ''} · {datetime(n.created_at)}
            </div>
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
