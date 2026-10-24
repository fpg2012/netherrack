import type { ThemePref } from '../lib/theme'
import { nextTheme, useTheme } from '../lib/theme'

/** 贴图取自 Minecraft 1.21 客户端资源（block/lantern.png、block/soul_lantern.png）：
 *  那张图是 16×48 的动画条，这里用的是侧面那一块（顶盖 + 灯身）加顶上的挂钩；
 *  日间那档把暖色压暗去饱和，当作没点着。 */
const LANTERNS: Record<ThemePref, { src: string; label: string }> = {
  system: { src: '/lantern/soul.png', label: '跟随系统（灵魂灯笼）' },
  light: { src: '/lantern/off.png', label: '日间（灯笼没点着）' },
  dark: { src: '/lantern/on.png', label: '夜间（灯笼亮着）' },
}

const WIDTH = 36
const HEIGHT = 62

/** 配色切换：从顶上垂下来的灯笼。只是一张图，没有按钮框。 */
export function ThemeLantern() {
  const { theme, setTheme } = useTheme()
  const now = LANTERNS[theme]
  const next = LANTERNS[nextTheme(theme)]

  return (
    <button
      type="button"
      className={`lantern-toggle is-${theme}`}
      aria-label={`配色：${now.label}，点击切到${next.label}`}
      onClick={() => setTheme(nextTheme(theme))}
    >
      {/* 同一张图再用一次，只留灯身当光晕（遮罩在里层，光晕在外层，见 CSS） */}
      <span className="lantern-glow" aria-hidden="true">
        <img src={now.src} alt="" width={WIDTH} height={HEIGHT} draggable={false} />
      </span>
      <img className="lantern" src={now.src} alt=""
           width={WIDTH} height={HEIGHT} draggable={false} />
      <span className="spark" />
      <span className="spark" />
      <span className="spark" />
    </button>
  )
}
