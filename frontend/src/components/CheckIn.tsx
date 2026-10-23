import { useState } from 'react'
import { useCheckIn, useDoCheckIn, useMe } from '../api/hooks'
import { checkInGreeting } from '../lib/checkin'
import { netherrackBurst } from '../lib/burst'
import { toast } from './Toast'

/** 侧栏里的每日签到：显示连续天数，并给出签到按钮。 */
export function CheckIn() {
  const status = useCheckIn()
  const checkIn = useDoCheckIn()
  const me = useMe()
  const data = status.data
  const name = me.data?.nickname || me.data?.username || '朋友'
  const done = data?.checked_in_today ?? false
  const [filling, setFilling] = useState(false)
  const completed = done && !filling

  return (
    <div className="checkin">
      <div className="checkin-meta">
        <span className="checkin-label">签到</span>
        <span className="checkin-days">
          {data
            ? data.current_streak > 0 ? `连续 ${data.current_streak} 天` : '今天还没签到'
            : '今日签到'}
        </span>
      </div>
      <button
        type="button"
        className={`checkin-btn${filling ? ' filling' : ''}${completed ? ' done' : ''}`}
        disabled={!data || done || filling || checkIn.isPending}
        onClick={(e) => {
          if (!data || done || filling) return
          const rect = e.currentTarget.getBoundingClientRect()
          const x = e.clientX || rect.left + rect.width / 2
          const y = e.clientY || rect.top + rect.height / 2
          const started = performance.now()
          setFilling(true)
          checkIn.mutate(undefined, {
            onSuccess: () => {
              const wait = Math.max(0, 2000 - (performance.now() - started))
              window.setTimeout(() => {
                setFilling(false)
                netherrackBurst(x, y)
                toast(checkInGreeting(name))
              }, wait)
            },
            onError: (err) => {
              setFilling(false)
              toast(err instanceof Error ? err.message : '签到失败')
            },
          })
        }}
      >
        <span>{filling ? '签到中…' : done ? '已签到' : '签到'}</span>
      </button>
    </div>
  )
}
