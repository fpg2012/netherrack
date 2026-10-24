import { Footer } from './Footer'
import { SidebarHeader } from './SidebarHeader'
import { TagBar } from './TagBar'
import type { TagWithCount } from '../types'

interface Meta {
  discussions: number
  posts: number
  users: number
}

/** 宽屏侧栏：导航、标签、站点统计、页脚。首页和帖子页共用。 */
export function Sidebar({ tags, meta, active = null, untaggedActive = false }: {
  tags: TagWithCount[]
  meta: (Meta & { untagged: number }) | undefined
  active?: string | null
  untaggedActive?: boolean
}) {
  return (
    <>
      <SidebarHeader />

      <h2>标签</h2>
      <TagBar
        tags={tags}
        untagged={meta?.untagged ?? 0}
        active={active}
        untaggedActive={untaggedActive}
        variant="sidebar"
      />

      <h2>站点</h2>
      <dl className="site-stats">
        <div><dt>讨论</dt><dd>{meta?.discussions ?? 0}</dd></div>
        <div><dt>帖子</dt><dd>{meta?.posts ?? 0}</dd></div>
        <div><dt>成员</dt><dd>{meta?.users ?? 0}</dd></div>
      </dl>

      <Footer variant="side" />
    </>
  )
}
