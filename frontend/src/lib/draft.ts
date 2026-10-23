import { useEffect, useState } from 'react'

/**
 * 把表单内容自动存到 localStorage，刷新/误关后能恢复。
 * 内容与初始值相同时删掉 key，避免留下空草稿。
 */
export function useDraft<T>(key: string, initial: T): [T, (value: T) => void, () => void] {
  const [value, setValue] = useState<T>(() => {
    try {
      const raw = window.localStorage.getItem(key)
      return raw ? (JSON.parse(raw) as T) : initial
    } catch {
      return initial
    }
  })

  useEffect(() => {
    const timer = window.setTimeout(() => {
      try {
        if (JSON.stringify(value) === JSON.stringify(initial)) {
          window.localStorage.removeItem(key)
        } else {
          window.localStorage.setItem(key, JSON.stringify(value))
        }
      } catch {
        /* 隐私模式下 localStorage 不可用，忽略 */
      }
    }, 400)
    return () => window.clearTimeout(timer)
  }, [key, value, initial])

  const clear = () => {
    try {
      window.localStorage.removeItem(key)
    } catch {
      /* ignore */
    }
    setValue(initial)
  }

  return [value, setValue, clear]
}
