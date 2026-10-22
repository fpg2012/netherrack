import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'

export interface MenuItem {
  label?: ReactNode
  onSelect?: () => void
  disabled?: boolean
  divider?: boolean
}

export function Dropdown({ label, items }: { label: string; items: MenuItem[] }) {
  const [open, setOpen] = useState(false)
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

  return (
    <div className="dropdown" ref={box}>
      <button
        type="button"
        className="dropdown-trigger"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        {label}
        <span className="caret" aria-hidden="true">▾</span>
      </button>
      {open && (
        <div className="dropdown-list" role="menu">
          {items.map((item, i) =>
            item.divider ? (
              <hr key={`d${i}`} />
            ) : (
              <button
                key={i}
                type="button"
                role="menuitem"
                disabled={item.disabled}
                onClick={() => {
                  setOpen(false)
                  item.onSelect?.()
                }}
              >
                {item.label}
              </button>
            ),
          )}
        </div>
      )}
    </div>
  )
}
