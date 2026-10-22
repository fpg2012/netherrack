import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMe, useUser, useUserDiscussions, useUserPosts } from '../api/hooks'
import { Avatar } from '../components/Avatar'
import { DiscussionCard } from '../components/DiscussionCard'
import { date, datetime } from '../lib/format'

export function UserPage() {
  const { id } = useParams()
  const userId = Number(id)
  const me = useMe()
  const profile = useUser(userId)
  const [tab, setTab] = useState<'discussions' | 'posts'>('discussions')
  const [page, setPage] = useState(1)
  const discussions = useUserDiscussions(userId, page)
  const posts = useUserPosts(userId, page)

  if (!me.data) return <p className="muted"><Link to="/login">登录</Link> 后查看用户资料。</p>
  if (profile.isLoading) return <p className="muted">加载中…</p>
  if (!profile.data) return <p>用户不存在。<Link to="/">返回</Link></p>
  const u = profile.data
  const current = tab === 'discussions' ? discussions.data : posts.data

  return (
    <>
      <div className="profile">
        <Avatar user={u} size={48} />
        <div>
          <h1>{u.nickname || u.username}</h1>
          <p className="muted small">
            {u.nickname && <>@{u.username} · </>}
            注册于 {date(u.joined_at)} · {u.discussions} 个讨论 · {u.posts} 条回复
            {u.is_admin && <span className="tag" style={{ '--tag': '#2e7d32' } as never}>管理</span>}
          </p>
          {u.bio && <p>{u.bio}</p>}
        </div>
      </div>

      <p className="tabs">
        <button type="button" className={tab === 'discussions' ? 'active' : ''}
                onClick={() => { setTab('discussions'); setPage(1) }}>讨论</button>
        <button type="button" className={tab === 'posts' ? 'active' : ''}
                onClick={() => { setTab('posts'); setPage(1) }}>回复</button>
      </p>

      {tab === 'discussions' ? (
        <div className="grid">
          {discussions.data?.items.map((d) => <DiscussionCard key={d.id} d={d} />)}
        </div>
      ) : (
        <ul className="posts-list">
          {posts.data?.items.map((p) => (
            <li key={p.post_id}>
              <Link to={`/d/${p.discussion_id}#p${p.post_id}`}>{p.discussion_title}</Link>
              <div className="muted small">#{p.number} · {datetime(p.created_at)}</div>
              <div className="snippet">{p.snippet}</div>
            </li>
          ))}
        </ul>
      )}
      {current?.total === 0 && <p className="muted">暂无内容。</p>}

      <p className="pager">
        {page > 1 && <a href="#" onClick={(e) => { e.preventDefault(); setPage(page - 1) }}>← 上一页</a>}
        <span>{page} / {current?.pages ?? 1}</span>
        {page < (current?.pages ?? 1) && (
          <a href="#" onClick={(e) => { e.preventDefault(); setPage(page + 1) }}>下一页 →</a>
        )}
      </p>
    </>
  )
}
