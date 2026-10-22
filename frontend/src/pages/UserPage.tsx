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
      <header className="profile">
        <Avatar user={u} size={64} />
        <div className="profile-body">
          <h1>
            {u.nickname || u.username}
            {u.nickname && <span className="handle">@{u.username}</span>}
            {u.is_admin && <span className="tag role">管理</span>}
          </h1>
          <ul className="profile-stats">
            <li><b>{u.discussions}</b>讨论</li>
            <li><b>{u.posts}</b>回复</li>
            <li>加入于 <time dateTime={u.joined_at}>{date(u.joined_at)}</time></li>
          </ul>
          {u.bio && <p className="profile-bio">{u.bio}</p>}
        </div>
      </header>

      <div className="tabs">
        <button type="button" className={tab === 'discussions' ? 'active' : ''}
                onClick={() => { setTab('discussions'); setPage(1) }}>
          讨论<span className="n">{u.discussions}</span>
        </button>
        <button type="button" className={tab === 'posts' ? 'active' : ''}
                onClick={() => { setTab('posts'); setPage(1) }}>
          回复<span className="n">{u.posts}</span>
        </button>
      </div>

      {tab === 'discussions' ? (
        <div className="grid">
          {discussions.data?.items.map((d) => <DiscussionCard key={d.id} d={d} />)}
        </div>
      ) : (
        <ul className="posts-list">
          {posts.data?.items.map((p) => (
            <li key={p.post_id}>
              <Link className="post-title" to={`/d/${p.discussion_id}#p${p.post_id}`}>
                {p.discussion_title}
              </Link>
              <p className="post-snippet">{p.snippet}</p>
              <div className="post-meta">#{p.number} · {datetime(p.created_at)}</div>
            </li>
          ))}
        </ul>
      )}
      {current?.total === 0 && <p className="muted">还没有内容。</p>}

      {(current?.pages ?? 1) > 1 && (
        <p className="pager">
          {page > 1 && <a href="#" onClick={(e) => { e.preventDefault(); setPage(page - 1) }}>← 上一页</a>}
          <span>{page} / {current?.pages ?? 1}</span>
          {page < (current?.pages ?? 1) && (
            <a href="#" onClick={(e) => { e.preventDefault(); setPage(page + 1) }}>下一页 →</a>
          )}
        </p>
      )}
    </>
  )
}
