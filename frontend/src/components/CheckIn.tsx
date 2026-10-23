import { useCheckIn, useDoCheckIn, useMe } from '../api/hooks'
import { checkInGreeting } from '../lib/checkin'
import { toast } from './Toast'

/** 侧栏里的每日签到：显示连续天数，并给出签到按钮。 */
export function CheckIn() {
  const status = useCheckIn()
  const checkIn = useDoCheckIn()
  const me = useMe()
  const data = status.data
  const name = me.data?.nickname || me.data?.username || '朋友'
  const done = data?.checked_in_today ?? false

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
        className="checkin-btn"
        disabled={!data || done || checkIn.isPending}
        onClick={() => checkIn.mutate(undefined, {
          onSuccess: () => toast(checkInGreeting(name)),
          onError: (err) => toast(err instanceof Error ? err.message : '签到失败'),
        })}
      >
        {done ? '已签到' : checkIn.isPending ? '签到中…' : '签到'}
      </button>
    </div>
  )
}
