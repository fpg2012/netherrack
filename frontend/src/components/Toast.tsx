import { useEffect, useState } from 'react'

// 极简全局 toast：模块级订阅，任何地方 import { toast } 就能用
type Listener = (text: string) => void
const listeners = new Set<Listener>()

export function toast(text: string) {
  listeners.forEach((fn) => fn(text))
}

interface Item {
  id: number
  text: string
}

let seq = 0

export function ToastHost() {
  const [items, setItems] = useState<Item[]>([])

  useEffect(() => {
    const push: Listener = (text) => {
      const id = ++seq
      setItems((prev) => [...prev, { id, text }])
      window.setTimeout(() => {
        setItems((prev) => prev.filter((item) => item.id !== id))
      }, 4000)
    }
    listeners.add(push)
    return () => {
      listeners.delete(push)
    }
  }, [])

  if (items.length === 0) return null
  return (
    <div className="toasts" role="status" aria-live="polite">
      {items.map((item) => (
        <div key={item.id} className="toast" onClick={() => setItems((prev) => prev.filter((i) => i.id !== item.id))}>
          {item.text}
        </div>
      ))}
    </div>
  )
}
