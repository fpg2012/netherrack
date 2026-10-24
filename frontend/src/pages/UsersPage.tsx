import { Fragment, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMe, useResetUserPassword, useSetUserActive, useUsers } from '../api/hooks'
import { Avatar } from '../components/Avatar'
import { Dropdown } from '../components/Dropdown'
import { toast } from '../components/Toast'
import { date } from '../lib/format'
import type { UserListItem } from '../types'

export function UsersPage() {
  const [page, setPage] = useState(1)
  const [input, setInput] = useState('')
  const [query, setQuery] = useState('')
  const me = useMe()
  const users = useUsers(page, query)
  const [resetId, setResetId] = useState<number | null>(null)
  const [newPassword, setNewPassword] = useState('')
  const [resetResult, setResetResult] = useState<{ userId: number; password: string } | null>(null)
  const resetPassword = useResetUserPassword(resetId ?? undefined)
  const setActive = useSetUserActive()

  if (!me.data) {
    return <p className="muted"><Link to="/login">登录</Link> 后才能查看用户列表。</p>
  }

  const isAdmin = me.data.is_admin

  const copyResetPassword = async () => {
    if (!resetResult) return
    try {
      await navigator.clipboard.writeText(resetResult.password)
      toast('新密码已复制')
    } catch {
      toast('复制失败，请手动选择密码')
    }
  }

  const toggleActive = (u: UserListItem) => {
    const nextActive = u.is_active === false
    if (!nextActive
        && !window.confirm(`封禁 ${u.nickname || u.username}？封禁后该用户将无法登录。`)) {
      return
    }
    setActive.mutate({ id: u.id, is_active: nextActive }, {
      onSuccess: () => {
        toast(nextActive ? '已解封' : '已封禁')
        if (resetId === u.id) setResetId(null)
      },
      onError: (err) => toast(err.message),
    })
  }

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
            {isAdmin && <th>操作</th>}
          </tr>
        </thead>
        <tbody>
          {users.data?.items.map((u) => (
            <Fragment key={u.id}>
              <tr>
                <td className="user-cell">
                  <Avatar user={{ ...u, avatar_path: u.avatar_path }} size={22} />
                  <Link to={`/u/${u.id}`}><strong>{u.nickname || u.username}</strong></Link>
                  {u.nickname && <span className="muted"> @{u.username}</span>}
                  {u.is_admin && <span className="tag" style={{ '--tag': '#2e7d32' } as never}>管理</span>}
                  {u.is_active === false && <span className="tag" style={{ '--tag': '#777' } as never}>封禁</span>}
                </td>
                <td className="muted">{date(u.joined_at)}</td>
                <td className="num">{u.posts}</td>
                <td className="num">{u.discussions}</td>
                {isAdmin && (
                  <td>
                    {u.id === me.data.id
                      ? <span className="muted">—</span>
                      : (
                        <Dropdown
                          label="操作"
                          items={[
                            {
                              label: u.is_active === false ? '解封' : '封禁',
                              disabled: setActive.isPending,
                              onSelect: () => toggleActive(u),
                            },
                            { divider: true },
                            {
                              label: '重置密码',
                              onSelect: () => {
                                setResetId(u.id)
                                setNewPassword('')
                                setResetResult(null)
                              },
                            },
                          ]}
                        />
                      )}
                  </td>
                )}
              </tr>
              {resetId === u.id && (
                <tr className="reset-row">
                  <td colSpan={isAdmin ? 5 : 4}>
                    {resetResult?.userId === u.id ? (
                      <div className="admin-reset-result">
                        <p className="muted small">
                          新密码只显示这一次。该用户需要重新登录，请尽快告知用户。
                        </p>
                        <div className="code-row">
                          <code>{resetResult.password}</code>
                          <button type="button" onClick={() => void copyResetPassword()}>复制</button>
                          <button
                            type="button"
                            onClick={() => { setResetId(null); setResetResult(null) }}
                          >
                            完成
                          </button>
                        </div>
                      </div>
                    ) : (
                      <form
                        className="reset-form"
                        onSubmit={(e) => {
                          e.preventDefault()
                          const password = newPassword.trim()
                          resetPassword.mutate(password || undefined, {
                            onSuccess: (data) => {
                              setResetResult({ userId: u.id, password: data.password })
                              setNewPassword('')
                              toast('密码已重置')
                            },
                            onError: (err) => toast(err.message),
                          })
                        }}
                      >
                        <input
                          type="password"
                          autoComplete="new-password"
                          minLength={8}
                          maxLength={128}
                          value={newPassword}
                          placeholder={`为 ${u.username} 设置新密码（留空自动生成）`}
                          aria-label="新密码"
                          onChange={(e) => setNewPassword(e.target.value)}
                        />
                        <button type="submit" disabled={resetPassword.isPending}>
                          {resetPassword.isPending ? '重置中…' : '确认重置'}
                        </button>
                        <button
                          type="button"
                          disabled={resetPassword.isPending}
                          onClick={() => { setResetId(null); setNewPassword('') }}
                        >
                          取消
                        </button>
                        <span className="muted small">重置后该用户需要重新登录</span>
                      </form>
                    )}
                  </td>
                </tr>
              )}
            </Fragment>
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
