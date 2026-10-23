/** 判断标签原色是否偏亮：偏亮的标签在浅色模式用浅底深字，保留黄绿/浅蓝的色相。 */
export function tagTone(color: string | null): 'light' | 'dark' {
  if (!color) return 'dark'
  const m = /^#([0-9a-f]{6})$/i.exec(color.trim())
  if (!m) return 'dark'
  const n = Number.parseInt(m[1], 16)
  const channels = [(n >> 16) & 255, (n >> 8) & 255, n & 255]
  const linear = channels.map((v) => {
    const c = v / 255
    return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
  })
  const luminance = 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
  return luminance > 0.43 ? 'light' : 'dark'
}
