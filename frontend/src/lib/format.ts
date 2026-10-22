import type { UserBrief } from '../types'

export function pad(n: number): string {
  return n.toString().padStart(2, '0')
}

/** 后端返回 ISO 时间，展示成 YYYY-MM-DD HH:MM */
export function datetime(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso.slice(0, 16)
  // 与旧站保持一致：直接展示 UTC 时间戳，不做时区换算
  return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())} ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`
}

export function date(iso: string | null): string {
  return datetime(iso).slice(0, 10)
}

export function displayName(user: UserBrief | null): string {
  if (!user) return '匿名'
  return user.nickname || user.username
}
