import { Link, NavLink, useNavigate, useSearchParams } from 'react-router-dom'
import { useMe, useUnreadCount } from '../api/hooks'
import { UserMenu } from './UserMenu'

export function Header() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const me = useMe()
  const unread = useUnreadCount()

  return (
    <header className="site-header">
      <Link className="brand" to="/" title="soulsand">
        <img src="/logo.png" alt="soulsand" width={26} height={26} />
        <span>soulsand</span>
      </Link>

      <nav className="nav">
        <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>讨论</NavLink>
        {me.data && (
          <NavLink to="/users" className={({ isActive }) => (isActive ? 'active' : '')}>用户</NavLink>
        )}
        {me.data && (
          <NavLink to="/notifications" className={({ isActive }) => (isActive ? 'active' : '')}>
            通知{unread.data?.count ? <span className="badge">{unread.data.count}</span> : null}
          </NavLink>
        )}
      </nav>

      <form
        className="search"
        onSubmit={(e) => {
          e.preventDefault()
          const q = new FormData(e.currentTarget).get('q')?.toString().trim()
          if (q) navigate(`/search?q=${encodeURIComponent(q)}`)
        }}
      >
        <input type="search" name="q" placeholder="搜索" defaultValue={params.get('q') ?? ''} />
        <button type="submit" aria-label="搜索">搜索</button>
      </form>

      <div className="auth">
        {me.data ? (
          <>
            <Link className="button" to="/new">发帖</Link>
            <UserMenu />
          </>
        ) : (
          <Link className="button" to="/login">登录</Link>
        )}
      </div>
    </header>
  )
}
