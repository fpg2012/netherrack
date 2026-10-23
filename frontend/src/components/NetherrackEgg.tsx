import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { useLocation } from 'react-router-dom'

type Hole = { id: number; x: number; y: number }

const BLOCKED = [
  'a', 'button', 'input', 'textarea', 'select', 'label', 'summary',
  '[contenteditable="true"]', '.card', '.post', '.sidebar', '.site-header',
  '.site-footer', '.side-footer', '.tbl', '.editor', '.tag', '.pager',
  '.profile', '.notice-form', '.invite-panel', '.tag-editor',
].join(',')

/** 在页面空白处狂点，有概率凿出一块地狱岩。 */
export function NetherrackEgg() {
  const [holes, setHoles] = useState<Hole[]>([])
  const { pathname } = useLocation()

  useEffect(() => { setHoles([]) }, [pathname])

  useEffect(() => {
    let last = 0
    let nextId = 1
    const onClick = (e: MouseEvent) => {
      if (e.button !== 0 || e.defaultPrevented) return
      const el = e.target as HTMLElement | null
      if (!el || el.closest(BLOCKED)) return
      const now = performance.now()
      if (now - last < 220) return
      if (Math.random() > 0.22) return
      last = now
      const hole = { id: nextId++, x: e.pageX, y: e.pageY }
      setHoles((prev) => [...prev.slice(-59), hole])
    }
    document.addEventListener('click', onClick)
    return () => document.removeEventListener('click', onClick)
  }, [])

  if (holes.length === 0) return null
  return createPortal(
    <div className="netherrack-holes" aria-hidden="true">
      {holes.map((h) => (
        <span key={h.id} className="netherrack-hole" style={{ left: h.x, top: h.y }} />
      ))}
    </div>,
    document.body,
  )
}
