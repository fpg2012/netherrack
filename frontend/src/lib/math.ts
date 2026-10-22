import katex from 'katex'
import renderMathInElement from 'katex/contrib/auto-render'
import 'katex/dist/katex.min.css'

/** 渲染 [data-tex] 元素，再处理正文里残留的 $...$ */
export function renderMath(root: HTMLElement | null): void {
  if (!root) return
  root.querySelectorAll<HTMLElement>('[data-tex]').forEach((el) => {
    try {
      katex.render(el.dataset.tex ?? '', el, {
        displayMode: el.classList.contains('math-display'),
        throwOnError: false,
      })
    } catch {
      /* 渲染失败保留原始文本 */
    }
  })
  renderMathInElement(root, {
    delimiters: [
      { left: '$$', right: '$$', display: true },
      { left: '$', right: '$', display: false },
    ],
    ignoredTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],
    ignoredClasses: ['katex', 'katex-display'],
    throwOnError: false,
  })
}
