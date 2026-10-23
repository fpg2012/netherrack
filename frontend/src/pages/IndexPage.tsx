import { useSearchParams } from 'react-router-dom'
import { useDiscussions, useMeta, useTags } from '../api/hooks'
import { DiscussionCard } from '../components/DiscussionCard'
import { Sidebar } from '../components/Sidebar'
import { TagBar } from '../components/TagBar'

export function IndexPage() {
  const [params, setParams] = useSearchParams()
  const tag = params.get('tag')
  const page = Math.max(1, Number(params.get('page') ?? 1))
  const discussions = useDiscussions({ page, tag })
  const tags = useTags()
  const meta = useMeta()
  const tagName = tags.data?.find((t) => t.slug === tag)?.name
  const loading = discussions.isPending

  const go = (next: number) => {
    const q = new URLSearchParams(params)
    q.set('page', String(next))
    setParams(q)
  }

  return (
    <>
      <div className="index-layout">
        <div className="index-main">
          <h1>{tagName ?? '全部讨论'}</h1>
          <p className="muted">
            {loading ? '加载中…' : `共 ${discussions.data?.total ?? 0} 个讨论`}
          </p>

          <TagBar
            tags={tags.data ?? []}
            total={meta.data?.discussions ?? 0}
            active={tag}
          />

          <div className="grid">
            {discussions.data?.items.map((d) => <DiscussionCard key={d.id} d={d} />)}
          </div>

          {!loading && discussions.data?.total === 0 && (
            <p className="muted">这里还没有公开的讨论。</p>
          )}
          {discussions.isError && (
            <p className="muted">加载失败：{String(discussions.error)}</p>
          )}

          <p className="pager">
            {page > 1 && <a href="#" onClick={(e) => { e.preventDefault(); go(page - 1) }}>← 上一页</a>}
            <span>{page} / {discussions.data?.pages ?? 1}</span>
            {page < (discussions.data?.pages ?? 1) && (
              <a href="#" onClick={(e) => { e.preventDefault(); go(page + 1) }}>下一页 →</a>
            )}
          </p>
        </div>

        <aside className="sidebar">
          <Sidebar
            tags={tags.data ?? []}
            total={meta.data?.discussions ?? 0}
            active={tag}
            meta={meta.data}
          />
        </aside>
      </div>
    </>
  )
}
