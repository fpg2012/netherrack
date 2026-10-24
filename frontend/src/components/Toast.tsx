import { useEffect, useRef, useState } from 'react'

// 极简全局 toast：模块级订阅，任何地方 import { toast } 就能用
export interface ToastOptions {
  /** 自动消失时间（毫秒）；0 表示常驻，需要手动 dismiss。 */
  duration?: number
  /** 0-1 的进度，传了会显示进度条。 */
  progress?: number
}

export type ToastId = number

type ToastEvent =
  | { type: 'push'; id: ToastId; text: string; progress?: number; duration: number }
  | { type: 'update'; id: ToastId; text?: string; progress?: number }
  | { type: 'dismiss'; id: ToastId }

const listeners = new Set<(event: ToastEvent) => void>()

let seq = 0

export function toast(text: string, options: ToastOptions = {}): ToastId {
  const id = ++seq
  listeners.forEach((fn) => fn({
    type: 'push',
    id,
    text,
    progress: options.progress,
    duration: options.duration ?? 4000,
  }))
  return id
}

export function updateToast(id: ToastId, text?: string, progress?: number) {
  listeners.forEach((fn) => fn({ type: 'update', id, text, progress }))
}

export function dismissToast(id: ToastId) {
  listeners.forEach((fn) => fn({ type: 'dismiss', id }))
}

interface Item {
  id: number
  text: string
  progress?: number
}

export function ToastHost() {
  const [items, setItems] = useState<Item[]>([])
  const timers = useRef(new Map<number, number>())

  useEffect(() => {
    const clearTimer = (id: number) => {
      const timer = timers.current.get(id)
      if (timer !== undefined) {
        window.clearTimeout(timer)
        timers.current.delete(id)
      }
    }

    const push: (event: ToastEvent) => void = (event) => {
      if (event.type === 'push') {
        setItems((prev) => [...prev, { id: event.id, text: event.text, progress: event.progress }])
        if (event.duration > 0) {
          const timer = window.setTimeout(() => {
            timers.current.delete(event.id)
            setItems((prev) => prev.filter((item) => item.id !== event.id))
          }, event.duration)
          timers.current.set(event.id, timer)
        }
        return
      }
      if (event.type === 'update') {
        setItems((prev) => prev.map((item) => item.id === event.id
          ? {
              ...item,
              text: event.text ?? item.text,
              progress: event.progress ?? item.progress,
            }
          : item))
        return
      }
      clearTimer(event.id)
      setItems((prev) => prev.filter((item) => item.id !== event.id))
    }

    listeners.add(push)
    return () => {
      listeners.delete(push)
      timers.current.forEach((timer) => window.clearTimeout(timer))
      timers.current.clear()
    }
  }, [])

  if (items.length === 0) return null
  return (
    <div className="toasts" role="status" aria-live="polite">
      {items.map((item) => (
        <div key={item.id} className="toast" onClick={() => dismissToast(item.id)}>
          <span>{item.text}</span>
          {item.progress !== undefined && (
            <span className="toast-progress" aria-hidden="true">
              <span style={{ width: `${Math.round(Math.min(1, Math.max(0, item.progress)) * 100)}%` }} />
            </span>
          )}
        </div>
      ))}
    </div>
  )
}
