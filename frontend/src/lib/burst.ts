const COLORS = ['#5c2a23', '#6b332b', '#7d3f35', '#8f4a3e', '#a85a4a', '#b8614f', '#3a1714']

/** 在鼠标位置炸出一把地狱岩颜色的像素粒子，约 1 秒内消失。 */
export function netherrackBurst(x: number, y: number): void {
  if (typeof document === 'undefined') return
  const layer = document.createElement('div')
  layer.className = 'netherrack-burst'
  layer.style.left = `${x}px`
  layer.style.top = `${y}px`

  for (let i = 0; i < 34; i += 1) {
    const p = document.createElement('i')
    const angle = Math.random() * Math.PI * 2
    const distance = 30 + Math.random() * 110
    const dx = Math.cos(angle) * distance
    const dy = Math.sin(angle) * distance
    const size = 4 + Math.floor(Math.random() * 7)
    p.style.setProperty('--dx', `${dx.toFixed(1)}px`)
    p.style.setProperty('--dy', `${dy.toFixed(1)}px`)
    p.style.setProperty('--rot', `${Math.round(Math.random() * 360)}deg`)
    p.style.width = `${size}px`
    p.style.height = `${size}px`
    p.style.background = COLORS[Math.floor(Math.random() * COLORS.length)]
    p.style.animationDelay = `${Math.round(Math.random() * 70)}ms`
    layer.appendChild(p)
  }

  document.body.appendChild(layer)
  window.setTimeout(() => layer.remove(), 1100)
}
