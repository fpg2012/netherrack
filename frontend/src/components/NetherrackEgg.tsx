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
    let clicks = 0
    let lastHole = 0
    let nextId = 1
    const onClick = (e: MouseEvent) => {
      if (e.button !== 0 || e.defaultPrevented) return
      const el = e.target as HTMLElement | null
      if (!el || el.closest(BLOCKED)) return
      clicks += 1
      // 前 5 次点击只当作挖矿前的试探，不会出东西
      if (clicks < 5) return
      if (Math.random() > 0.22) return
      const now = performance.now()
      if (now - lastHole < 120) return
      // 对齐到 72px 网格，取点击位置所在格的左上角
      const x = Math.floor(e.pageX / 72) * 72
      const y = Math.floor(e.pageY / 72) * 72
      // 整格必须都在空白处，避免压到卡片或正文
      const vx = x - window.scrollX
      const vy = y - window.scrollY
      for (const [dx, dy] of [[4, 4], [68, 4], [4, 68], [68, 68], [36, 36]]) {
        const under = document.elementFromPoint(vx + dx, vy + dy)
        if (under?.closest(BLOCKED)) return
      }
      lastHole = now
      const hole = { id: nextId++, x, y }
      setHoles((prev) => [...prev.slice(-59), hole])
    }
    document.addEventListener('click', onClick)
    return () => document.removeEventListener('click', onClick)
  }, [pathname])

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
