// 过高的代码块和图片折叠起来，点按钮展开。
// 直接操作 DOM：正文是 dangerouslySetInnerHTML 渲染的，没有 React 节点可用。

const PRE_LIMIT = 480
const IMG_LIMIT = 560

function makeToggle(label: string, onClick: () => void): HTMLButtonElement {
  const button = document.createElement('button')
  button.type = 'button'
  button.className = 'fold-toggle'
  button.textContent = label
  button.addEventListener('click', onClick)
  return button
}

function foldPre(pre: HTMLPreElement): void {
  if (pre.dataset.folded === '1') return
  if (pre.scrollHeight <= PRE_LIMIT) return
  pre.dataset.folded = '1'
  pre.classList.add('is-folded')

  const lines = (pre.textContent ?? '').split('\n').length
  const toggle = makeToggle(`展开代码（共 ${lines} 行）`, () => {
    const folded = pre.classList.toggle('is-folded')
    toggle.textContent = folded ? `展开代码（共 ${lines} 行）` : '收起代码'
  })
  pre.after(toggle)
}

function foldImage(img: HTMLImageElement): void {
  if (img.dataset.folded === '1' || !img.complete) return
  const box = img.closest('.img-fold') as HTMLElement | null
  if (box) return
  // 按当前宽度算图片会占多高，小图标不动
  const width = img.clientWidth || img.naturalWidth
  if (!img.naturalWidth || !width) return
  const height = (img.naturalHeight / img.naturalWidth) * width
  if (height <= IMG_LIMIT) return

  const parent = img.parentElement
  const target =
    parent && parent.tagName === 'A' && parent.childElementCount === 1 ? parent : img
  const wrap = document.createElement('div')
  wrap.className = 'img-fold is-folded'
  target.parentElement?.insertBefore(wrap, target)
  wrap.appendChild(target)

  img.dataset.folded = '1'
  const toggle = makeToggle('展开图片', () => {
    const folded = wrap.classList.toggle('is-folded')
    toggle.textContent = folded ? '展开图片' : '收起图片'
  })
  wrap.after(toggle)
}

/** 给容器里的 pre / img 加折叠；返回清理函数。 */
export function setupFolding(root: HTMLElement | null): () => void {
  if (!root) return () => {}
  const listeners: Array<() => void> = []

  for (const pre of root.querySelectorAll('pre')) {
    if (!pre.closest('.img-fold')) foldPre(pre as HTMLPreElement)
  }

  for (const img of root.querySelectorAll('img')) {
    if (img.classList.contains('emoji') || img.dataset.folded === '1') continue
    const onLoad = () => foldImage(img)
    if (img.complete) {
      foldImage(img)
    } else {
      img.addEventListener('load', onLoad, { once: true })
      listeners.push(() => img.removeEventListener('load', onLoad))
    }
  }

  return () => listeners.forEach((off) => off())
}
