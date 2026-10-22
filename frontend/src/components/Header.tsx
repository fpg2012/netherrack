import { Link, NavLink, useNavigate, useSearchParams } from 'react-router-dom'
import { useLogout, useMe } from '../api/hooks'
import { Avatar } from './Avatar'

export function Header() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const me = useMe()
  const logout = useLogout()

  return (
    <header className="site-header">
      <Link className="brand" to="/" title="soulsand">
        <img src="/logo.png" alt="soulsand" width={26} height={26} />
        <span>soulsand</span>
      </Link>

      <nav className="nav">
        <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>讨论</NavLink>
        <NavLink to="/users" className={({ isActive }) => (isActive ? 'active' : '')}>用户</NavLink>
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
            <Avatar user={me.data} size={22} />
            <span className="who">{me.data.nickname ?? me.data.username}</span>
            <button type="button" className="linklike" disabled={logout.isPending}
                    onClick={() => logout.mutate()}>
              退出
            </button>
          </>
        ) : (
          <Link className="button" to="/login">登录</Link>
        )}
      </div>
    </header>
  )
}
