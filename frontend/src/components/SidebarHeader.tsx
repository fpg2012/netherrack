import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useLogout, useMe, useUnreadCount } from '../api/hooks'
import { Avatar } from './Avatar'

const displayName = (u: { nickname: string | null; username: string }) =>
  u.nickname || u.username

/** 宽屏首页/帖子页没有顶栏，导航和账号操作都放在侧栏。 */
export function SidebarHeader() {
  const me = useMe()
  const unread = useUnreadCount()
  const logout = useLogout()
  const navigate = useNavigate()
  const [q, setQ] = useState('')

  return (
    <div className="side-nav">
      <Link className="brand" to="/" title="soulsand">
        <img src="/logo.png" alt="soulsand" width={26} height={26} />
        <span>soulsand</span>
      </Link>

      {me.data && (
        <>
          <nav className="links">
            <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>讨论</NavLink>
            <NavLink to="/users" className={({ isActive }) => (isActive ? 'active' : '')}>用户</NavLink>
            <NavLink to="/notifications" className={({ isActive }) => (isActive ? 'active' : '')}>
              通知{unread.data?.count ? <span className="badge">{unread.data.count}</span> : null}
            </NavLink>
          </nav>

          <form
            className="side-search"
            onSubmit={(e) => {
              e.preventDefault()
              const text = q.trim()
              if (text) navigate(`/search?q=${encodeURIComponent(text)}`)
            }}
          >
            <input
              type="search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="搜索"
              aria-label="搜索"
            />
            <button type="submit">搜索</button>
          </form>
        </>
      )}

      {me.data ? (
        <>
          <div className="side-user">
            <Link className="who" to={`/u/${me.data.id}`}>
              <Avatar user={me.data} size={22} />
              <span>{displayName(me.data)}</span>
            </Link>
            <Link className="button" to="/new">发帖</Link>
          </div>

          <div className="side-links">
            <Link to={`/u/${me.data.id}`}>个人主页</Link>
            <Link to="/settings">设置</Link>
            {me.data.is_admin && <Link to="/invites">邀请码</Link>}
            {me.data.is_admin && <Link to="/notifications?send=1">系统通知</Link>}
          </div>

          <div className="side-logout">
            <button type="button" disabled={logout.isPending} onClick={() => logout.mutate()}>
              退出登录
            </button>
          </div>
        </>
      ) : (
        <div className="side-user">
          <span className="muted">游客</span>
          <Link className="button" to="/login">登录</Link>
        </div>
      )}
    </div>
  )
}
