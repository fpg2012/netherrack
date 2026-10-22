import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useMe, useSearch } from '../api/hooks'
import { date, displayName } from '../lib/format'

export function SearchPage() {
  const [params] = useSearchParams()
  const q = params.get('q') ?? ''
  const [page, setPage] = useState(1)
  const me = useMe()
  const results = useSearch(q, page)

  if (!me.data) {
    return (
      <>
        <h1>搜索</h1>
        <p className="muted"><Link to="/login">登录</Link> 后才能搜索站内内容。</p>
      </>
    )
  }

  return (
    <>
      <h1>搜索</h1>
      <p className="muted">
        {q ? <>&quot;{q}&quot; 命中 {results.data?.total ?? 0} 帖</> : '输入关键词'}
      </p>

      <div className="grid">
        {results.data?.items.map((r) => (
          <div className="card" key={r.post_id}>
            <Link className="card-title" to={`/d/${r.discussion_id}#p${r.post_id}`}>
              #{r.discussion_id} {r.discussion_title}
            </Link>
            <div className="card-meta">{displayName(r.author)} · {date(r.created_at)}</div>
            <p className="card-snippet">{r.snippet}</p>
          </div>
        ))}
      </div>

      <p className="pager">
        {page > 1 && <a href="#" onClick={(e) => { e.preventDefault(); setPage(page - 1) }}>← 上一页</a>}
        <span>{page} / {results.data?.pages ?? 1}</span>
        {page < (results.data?.pages ?? 1) && (
          <a href="#" onClick={(e) => { e.preventDefault(); setPage(page + 1) }}>下一页 →</a>
        )}
      </p>
    </>
  )
}
