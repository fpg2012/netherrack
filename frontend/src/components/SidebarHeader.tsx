import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useMe, useUnreadCount } from '../api/hooks'
import { UserMenu } from './UserMenu'

/** 宽屏首页没有顶栏，导航整体放进侧栏。 */
export function SidebarHeader() {
  const me = useMe()
  const unread = useUnreadCount()
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

      <div className="side-actions">
        {me.data ? (
          <>
            <Link className="button" to="/new">发帖</Link>
            <UserMenu />
          </>
        ) : (
          <Link className="button" to="/login">登录</Link>
        )}
      </div>
    </div>
  )
}
