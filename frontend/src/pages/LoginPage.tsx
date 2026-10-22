import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'

export function LoginPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  return (
    <>
      <h1>登录</h1>
      <form
        className="narrow"
        onSubmit={async (e) => {
          e.preventDefault()
          setBusy(true)
          setError(null)
          const data = new FormData(e.currentTarget)
          try {
            await api.post('/auth/login', {
              username: data.get('username'),
              password: data.get('password'),
            })
            await queryClient.invalidateQueries()
            navigate('/')
          } catch (err) {
            setError(err instanceof Error ? err.message : '登录失败')
          } finally {
            setBusy(false)
          }
        }}
      >
        <p><label>用户名<br /><input name="username" autoComplete="username" required /></label></p>
        <p><label>密码<br /><input name="password" type="password" autoComplete="current-password" required /></label></p>
        {error && <p className="event">{error}</p>}
        <p><button type="submit" disabled={busy}>{busy ? '登录中…' : '登录'}</button></p>
      </form>
    </>
  )
}
