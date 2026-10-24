import { useSyncExternalStore } from 'react'

/**
 * 配色：system 跟随系统，light/dark 是用户手动选的（存 localStorage）。
 * 三态都要能表达，所以不像常见做法那样只存一个布尔。
 */
export type ThemePref = 'system' | 'light' | 'dark'

export const THEME_LABELS: Record<ThemePref, string> = {
  system: '跟随系统',
  light: '浅色',
  dark: '深色',
}

/** 点一下换下一档：跟随系统 → 浅色 → 深色 */
export function nextTheme(pref: ThemePref): ThemePref {
  if (pref === 'system') return 'light'
  if (pref === 'light') return 'dark'
  return 'system'
}

const KEY = 'theme'
const listeners = new Set<() => void>()
const media = window.matchMedia('(prefers-color-scheme: dark)')

function read(): ThemePref {
  try {
    const raw = window.localStorage.getItem(KEY)
    return raw === 'light' || raw === 'dark' ? raw : 'system'
  } catch {
    // 隐私模式下 localStorage 不可用，按系统配色走
    return 'system'
  }
}

let pref: ThemePref = read()

function resolve(p: ThemePref): 'light' | 'dark' {
  if (p === 'system') return media.matches ? 'dark' : 'light'
  return p
}

/** 把解析后的配色写到 <html>，样式表里全是 [data-theme="dark"] 这种选择器 */
function applyTheme(): void {
  const root = document.documentElement
  const now = resolve(pref)
  root.dataset.theme = now
  // 让滚动条、表单控件、默认画布也一起变
  root.style.colorScheme = now
}

export function initTheme(): void {
  applyTheme()
  // 只有「跟随系统」时才关心系统切换
  media.addEventListener('change', () => {
    if (pref === 'system') applyTheme()
  })
}

export function setTheme(next: ThemePref): void {
  pref = next
  try {
    if (next === 'system') window.localStorage.removeItem(KEY)
    else window.localStorage.setItem(KEY, next)
  } catch {
    /* 隐私模式忽略，本次会话内仍然生效 */
  }
  applyTheme()
  for (const fn of listeners) fn()
}

function subscribe(fn: () => void): () => void {
  listeners.add(fn)
  return () => {
    listeners.delete(fn)
  }
}

export function useTheme(): { theme: ThemePref; setTheme: (p: ThemePref) => void } {
  return { theme: useSyncExternalStore(subscribe, () => pref), setTheme }
}
