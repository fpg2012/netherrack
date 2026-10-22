import { useState } from 'react'
import { useUsers } from '../api/hooks'
import { date } from '../lib/format'

export function UsersPage() {
  const [page, setPage] = useState(1)
  const [input, setInput] = useState('')
  const [query, setQuery] = useState('')
  const users = useUsers(page, query)

  return (
    <>
      <h1>用户</h1>
      <p className="muted">共 {users.data?.total ?? 0} 人</p>

      <form
        className="inline-form"
        onSubmit={(e) => { e.preventDefault(); setPage(1); setQuery(input.trim()) }}
      >
        <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="按用户名筛选" />
        <button type="submit">筛选</button>
      </form>

      <table className="tbl users">
        <thead>
          <tr>
            <th>用户名</th>
            <th>注册于</th>
            <th className="num">帖子</th>
            <th className="num">讨论</th>
          </tr>
        </thead>
        <tbody>
          {users.data?.items.map((u) => (
            <tr key={u.id}>
              <td>
                <strong>{u.nickname || u.username}</strong>
                {u.nickname && <span className="muted"> @{u.username}</span>}
                {u.is_admin && <span className="tag" style={{ '--tag': '#2e7d32' } as never}>管理</span>}
              </td>
              <td className="muted">{date(u.joined_at)}</td>
              <td className="num">{u.posts}</td>
              <td className="num">{u.discussions}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <p className="pager">
        {page > 1 && <a href="#" onClick={(e) => { e.preventDefault(); setPage(page - 1) }}>← 上一页</a>}
        <span>{page} / {users.data?.pages ?? 1}</span>
        {page < (users.data?.pages ?? 1) && (
          <a href="#" onClick={(e) => { e.preventDefault(); setPage(page + 1) }}>下一页 →</a>
        )}
      </p>
    </>
  )
}
