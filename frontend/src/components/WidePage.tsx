import { Outlet } from 'react-router-dom'
import { useMeta, useTags } from '../api/hooks'
import { Sidebar } from './Sidebar'

/** 宽屏下带侧栏的通用页面容器；窄屏时自动退回单列。 */
export function WidePage() {
  const tags = useTags()
  const meta = useMeta()

  return (
    <div className="thread-layout">
      <div className="thread-main">
        <Outlet />
      </div>
      <aside className="sidebar">
        <Sidebar tags={tags.data ?? []} meta={meta.data} />
      </aside>
    </div>
  )
}
