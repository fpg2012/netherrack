import type { UserBrief } from '../types'

export function pad(n: number): string {
  return n.toString().padStart(2, '0')
}

// 站点时区由 /meta 下发，默认东八区；只影响展示，数据库统一存 UTC
let siteTimezone = 'Asia/Shanghai'

export function setSiteTimezone(tz: string | undefined): void {
  if (tz) siteTimezone = tz
}

function parts(iso: string): Record<string, string> | null {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return null
  const fmt = new Intl.DateTimeFormat('en-CA', {
    timeZone: siteTimezone,
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  })
  return Object.fromEntries(fmt.formatToParts(d).map((p) => [p.type, p.value]))
}

/** 后端返回 ISO(UTC) 时间，按站点时区展示成 YYYY-MM-DD HH:MM */
export function datetime(iso: string | null): string {
  if (!iso) return ''
  const p = parts(iso)
  if (!p) return iso.slice(0, 16)
  return `${p.year}-${p.month}-${p.day} ${p.hour}:${p.minute}`
}

export function date(iso: string | null): string {
  return datetime(iso).slice(0, 10)
}

export function displayName(user: UserBrief | null): string {
  if (!user) return '匿名'
  return user.nickname || user.username
}
