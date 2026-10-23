import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useLogout, useMe } from '../api/hooks'
import { Avatar } from './Avatar'

export function UserMenu() {
  const me = useMe()
  const logout = useLogout()
  const [open, setOpen] = useState(false)
  const [confirming, setConfirming] = useState(false)
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

  // 点了「退出登录」后 4 秒内没有再次确认就恢复，避免误触
  useEffect(() => {
    if (!confirming) return
    const timer = window.setTimeout(() => setConfirming(false), 4000)
    return () => window.clearTimeout(timer)
  }, [confirming])

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

          <div className="usermenu-sep" role="separator" />

          <button
            type="button"
            role="menuitem"
            className={confirming ? 'usermenu-logout confirm' : 'usermenu-logout'}
            disabled={logout.isPending}
            onClick={() => {
              if (!confirming) {
                setConfirming(true)
                return
              }
              setOpen(false)
              setConfirming(false)
              logout.mutate()
            }}
          >
            {confirming ? '再点一次确认退出' : '退出登录'}
          </button>
        </div>
      )}
    </div>
  )
}
