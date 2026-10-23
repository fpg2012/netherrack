import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="notfound">
      <h1 className="notfound-code" aria-label="页面不存在">404</h1>
      <p className="notfound-text">这里只有地狱岩。</p>
      <p className="muted">你要找的页面可能被挖走了，或者从来没有存在过。</p>
      <Link className="button" to="/">返回首页</Link>
    </div>
  )
}
