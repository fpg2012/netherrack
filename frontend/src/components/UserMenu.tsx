import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useCheckIn, useDoCheckIn, useLogout, useMe } from '../api/hooks'
import { Avatar } from './Avatar'
import { toast } from './Toast'
import { checkInGreeting } from '../lib/checkin'
import { netherrackBurst } from '../lib/burst'
import { nextTheme, THEME_LABELS, useTheme } from '../lib/theme'

export function UserMenu() {
  const me = useMe()
  const { theme, setTheme } = useTheme()
  const logout = useLogout()
  const checkin = useCheckIn()
  const doCheckIn = useDoCheckIn()
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
          <button
            type="button"
            role="menuitem"
            aria-label={`配色：${THEME_LABELS[theme]}，点击切换`}
            onClick={() => setTheme(nextTheme(theme))}
          >
            配色：{THEME_LABELS[theme]}
          </button>
          <button
            type="button"
            role="menuitem"
            disabled={!checkin.data || checkin.data.checked_in_today || doCheckIn.isPending}
            onClick={(e) => {
              const rect = e.currentTarget.getBoundingClientRect()
              const x = e.clientX || rect.left + rect.width / 2
              const y = e.clientY || rect.top + rect.height / 2
              setOpen(false)
              doCheckIn.mutate(undefined, {
                onSuccess: () => {
                  netherrackBurst(x, y)
                  toast(checkInGreeting(name))
                },
                onError: (err) => toast(err instanceof Error ? err.message : '签到失败'),
              })
            }}
          >
            {checkin.data?.checked_in_today
              ? `今日已签到 · 连续 ${checkin.data.current_streak} 天`
              : '签到'}
          </button>
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
