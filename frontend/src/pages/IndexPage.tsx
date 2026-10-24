import { useSearchParams } from 'react-router-dom'
import { useDiscussions, useMeta, useTags } from '../api/hooks'
import { DiscussionCard } from '../components/DiscussionCard'
import { Sidebar } from '../components/Sidebar'
import { TagBar } from '../components/TagBar'

export function IndexPage() {
  const [params, setParams] = useSearchParams()
  const tagParam = params.get('tag')
  const untagged = params.get('untagged') === '1'
  const all = params.get('all') === '1'
  const page = Math.max(1, Number(params.get('page') ?? 1))
  const tags = useTags()
  const meta = useMeta()
  // 站点配了默认板块时，不带参数的首页就是那个板块；「全部」要显式点
  const defaultTag = meta.data?.default_tag ?? null
  const tag = untagged ? null : (tagParam ?? (all ? null : defaultTag))
  const discussions = useDiscussions({ page, tag, untagged })
  const tagName = untagged ? null : tags.data?.find((t) => t.slug === tag)?.name
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
          <h1>{untagged ? '无标签' : tagName ?? '全部讨论'}</h1>
          <p className="muted">
            {loading ? '加载中…' : `共 ${discussions.data?.total ?? 0} 个讨论`}
          </p>

          <TagBar
            tags={tags.data ?? []}
            untagged={meta.data?.untagged ?? 0}
            total={meta.data?.discussions ?? 0}
            active={tag}
            untaggedActive={untagged}
            showAll={!!defaultTag}
            allActive={all}
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
            active={tag}
            untaggedActive={untagged}
            allActive={all}
            meta={meta.data}
          />
        </aside>
      </div>
    </>
  )
}
