import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useLogout, useMe } from '../api/hooks'
import { Avatar } from './Avatar'

export function UserMenu() {
  const me = useMe()
  const logout = useLogout()
  const [open, setOpen] = useState(false)
  const box = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onDown = (e: MouseEvent) => {
      if (!box.current?.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  if (!me.data) return null
  const name = me.data.nickname ?? me.data.username

  return (
    <div className="usermenu" ref={box}>
      <button
        type="button"
        className="usermenu-trigger"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <Avatar user={me.data} size={22} />
        <span className="who">{name}</span>
        <span className="caret" aria-hidden="true">▾</span>
      </button>

      {open && (
        <div className="usermenu-list" role="menu">
          <Link to={`/u/${me.data.id}`} role="menuitem" onClick={() => setOpen(false)}>
            个人主页
          </Link>
          <Link to="/settings" role="menuitem" onClick={() => setOpen(false)}>
            设置
          </Link>
          {me.data.is_admin && (
            <>
              <Link to="/invites" role="menuitem" onClick={() => setOpen(false)}>
                邀请码
              </Link>
              <Link to="/notifications?send=1" role="menuitem" onClick={() => setOpen(false)}>
                发送系统通知
              </Link>
            </>
          )}
          <button
            type="button"
            role="menuitem"
            disabled={logout.isPending}
            onClick={() => {
              setOpen(false)
              logout.mutate()
            }}
          >
            退出登录
          </button>
        </div>
      )}
    </div>
  )
}
