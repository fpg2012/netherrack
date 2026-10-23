import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'

export function RegisterPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [params] = useSearchParams()
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  return (
    <>
      <h1>注册</h1>
      <p className="muted">需要邀请码。邀请码由管理员发放，只能使用一次。</p>
      <form
        className="narrow"
        onSubmit={async (e) => {
          e.preventDefault()
          setBusy(true)
          setError(null)
          const data = new FormData(e.currentTarget)
          try {
            await api.post('/auth/register', {
              code: data.get('code'),
              username: data.get('username'),
              email: data.get('email'),
              password: data.get('password'),
              nickname: data.get('nickname') || null,
            })
            await queryClient.invalidateQueries()
            navigate('/')
          } catch (err) {
            setError(err instanceof Error ? err.message : '注册失败')
          } finally {
            setBusy(false)
          }
        }}
      >
        <p>
          <label>邀请码<br />
            <input name="code" defaultValue={params.get('code') ?? ''} autoComplete="off"
              required placeholder="XXXXX-XXXXX-XXXXX-XXXXX" />
          </label>
        </p>
        <p><label>用户名<br /><input name="username" autoComplete="username" required
          pattern="[A-Za-z0-9_\-]{3,32}" placeholder="3-32 位字母、数字、_ 或 -" /></label></p>
        <p><label>邮箱<br /><input name="email" type="email" autoComplete="email" required /></label></p>
        <p><label>密码<br /><input name="password" type="password" autoComplete="new-password"
          minLength={10} required placeholder="至少 10 位" /></label></p>
        <p><label>昵称（可选）<br /><input name="nickname" autoComplete="nickname" maxLength={64} /></label></p>
        {error && <p className="event">{error}</p>}
        <p><button type="submit" disabled={busy}>{busy ? '注册中…' : '注册'}</button></p>
      </form>
      <p className="muted">已有账号？<Link to="/login">去登录</Link></p>
    </>
  )
}
