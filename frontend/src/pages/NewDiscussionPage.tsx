import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useCreateDiscussion, useMe, useTags } from '../api/hooks'
import { MarkdownEditor } from '../components/MarkdownEditor'

export function NewDiscussionPage() {
  const navigate = useNavigate()
  const me = useMe()
  const tags = useTags()
  const create = useCreateDiscussion()

  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [picked, setPicked] = useState<string[]>([])

  if (!me.data) {
    return <p className="muted"><Link to="/login">登录</Link> 后才能发帖。</p>
  }

  return (
    <>
      <h1>发新帖</h1>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          create.mutate(
            { title, body_md: body, tags: picked },
            { onSuccess: (d) => navigate(`/d/${d.id}`) },
          )
        }}
      >
        <p>
          <input
            className="title-input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="标题"
            minLength={2}
            maxLength={200}
            required
          />
        </p>

        <fieldset className="tags-picker">
          <legend>板块（最多 5 个）</legend>
          {tags.data?.map((t) => (
            <label key={t.id}>
              <input
                type="checkbox"
                checked={picked.includes(t.slug)}
                disabled={!picked.includes(t.slug) && picked.length >= 5}
                onChange={(e) =>
                  setPicked(e.target.checked
                    ? [...picked, t.slug]
                    : picked.filter((s) => s !== t.slug))
                }
              />
              {t.name}
            </label>
          ))}
        </fieldset>

        <MarkdownEditor value={body} onChange={setBody} rows={14}
                        placeholder="正文，支持 Markdown 与 $公式$" />

        {create.isError && <p className="event">发布失败：{String(create.error)}</p>}
        <p>
          <button type="submit" disabled={create.isPending || !title.trim() || !body.trim()}>
            {create.isPending ? '发布中…' : '发布'}
          </button>
        </p>
      </form>
    </>
  )
}
