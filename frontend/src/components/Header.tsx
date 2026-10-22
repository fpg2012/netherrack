import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useLogout, useMe } from '../api/hooks'

export function Header() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const me = useMe()
  const logout = useLogout()

  return (
    <header>
      <Link className="brand" to="/" title="soulsand">
        <img src="/logo.png" alt="soulsand" width={26} height={26} />
      </Link>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          const q = new FormData(e.currentTarget).get('q')?.toString().trim()
          if (q) navigate(`/search?q=${encodeURIComponent(q)}`)
        }}
      >
        <input type="search" name="q" defaultValue={params.get('q') ?? ''} />
        <button type="submit">搜索</button>
      </form>
      <span className="auth">
        {me.data ? (
          <>
            <Link to="/new">发帖</Link>
            <Link to="/users">用户</Link>
            <span className="muted">{me.data.nickname ?? me.data.username}</span>
            <button
              type="button"
              className="linklike"
              disabled={logout.isPending}
              onClick={() => logout.mutate()}
            >
              退出
            </button>
          </>
        ) : (
          <>
            <Link to="/users">用户</Link>
            <Link to="/login">登录</Link>
          </>
        )}
      </span>
    </header>
  )
}
