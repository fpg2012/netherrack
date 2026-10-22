import { useEffect, useRef, useState } from 'react'
import { useAllUsers, usePreview } from '../api/hooks'
import { api } from '../api/client'
import { Avatar } from './Avatar'
import { setupFolding } from '../lib/fold'
import { renderMath } from '../lib/math'

interface Props {
  value: string
  onChange: (value: string) => void
  rows?: number
  placeholder?: string
  allowUpload?: boolean
}

/** 量出光标在 textarea 里的位置（用等宽镜像元素）。 */
function caretPosition(el: HTMLTextAreaElement): { top: number; left: number } {
  const style = getComputedStyle(el)
  const mirror = document.createElement('div')
  const props = [
    'boxSizing', 'width', 'paddingTop', 'paddingRight', 'paddingBottom', 'paddingLeft',
    'borderTopWidth', 'borderRightWidth', 'borderBottomWidth', 'borderLeftWidth',
    'fontFamily', 'fontSize', 'fontWeight', 'fontStyle', 'letterSpacing', 'lineHeight',
    'textTransform', 'wordSpacing',
  ] as const
  Object.assign(mirror.style, {
    position: 'absolute',
    visibility: 'hidden',
    top: '0',
    left: '0',
    whiteSpace: 'pre-wrap',
    wordWrap: 'break-word',
    overflowWrap: 'break-word',
  })
  for (const prop of props) mirror.style[prop] = style[prop]
  mirror.style.width = `${el.clientWidth}px`
  mirror.textContent = el.value.slice(0, el.selectionStart)
  const marker = document.createElement('span')
  marker.textContent = '\u200b'
  mirror.appendChild(marker)
  document.body.appendChild(mirror)
  const { offsetTop: top, offsetLeft: left } = marker
  document.body.removeChild(mirror)
  return {
    top: top - el.scrollTop + el.clientHeight * 0 + 2,
    left: Math.max(0, Math.min(left - el.scrollLeft, el.clientWidth - 210)),
  }
}

interface UploadResult {
  url: string
  filename: string
  mime: string
}

export function MarkdownEditor({
  value, onChange, rows = 10, placeholder, allowUpload = true,
}: Props) {
  const preview = usePreview()
  const box = useRef<HTMLDivElement>(null)
  const area = useRef<HTMLTextAreaElement>(null)
  const picker = useRef<HTMLInputElement>(null)
  const [showPreview, setShowPreview] = useState(false)
  const users = useAllUsers()
  const [mention, setMention] = useState<{ start: number; query: string } | null>(null)
  const [caret, setCaret] = useState({ top: 0, left: 0 })
  const [active, setActive] = useState(0)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!showPreview || !preview.data) return
    renderMath(box.current)
    return setupFolding(box.current)
  }, [showPreview, preview.data])

  const candidates = mention
    ? (users.data?.items ?? [])
        .filter((u) => {
          const q = mention.query.toLowerCase()
          return u.username.toLowerCase().startsWith(q)
            || (u.nickname ?? '').toLowerCase().startsWith(q)
        })
        .slice(0, 8)
    : []

  // 光标前面是不是正在输入 @xxx
  const detectMention = (el: HTMLTextAreaElement) => {
    const before = el.value.slice(0, el.selectionStart)
    const match = /(?:^|[\s(（>])@([A-Za-z0-9_\u4e00-\u9fff-]*)$/.exec(before)
    if (!match) return setMention(null)
    setMention({ start: el.selectionStart - match[1].length - 1, query: match[1] })
    setCaret(caretPosition(el))
    setActive(0)
  }

  const chooseMention = (username: string) => {
    const el = area.current
    if (!el || !mention) return
    const end = el.selectionStart
    const next = value.slice(0, mention.start) + `@${username} ` + value.slice(end)
    onChange(next)
    setMention(null)
    requestAnimationFrame(() => {
      el.focus()
      const pos = mention.start + username.length + 2
      el.setSelectionRange(pos, pos)
    })
  }

  const insert = (text: string) => {
    const el = area.current
    if (!el) return onChange(value + text)
    const start = el.selectionStart ?? value.length
    const end = el.selectionEnd ?? value.length
    onChange(value.slice(0, start) + text + value.slice(end))
    requestAnimationFrame(() => {
      el.focus()
      const pos = start + text.length
      el.setSelectionRange(pos, pos)
    })
  }

  const upload = async (file: File) => {
    setUploading(true)
    setError(null)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await api.postForm<UploadResult>('/uploads', form)
      const snippet = res.mime.startsWith('image/')
        ? `![](${res.url})`
        : `[${res.filename}](${res.url})`
      insert(snippet)
    } catch (err) {
      setError(err instanceof Error ? err.message : '上传失败')
    } finally {
      setUploading(false)
      if (picker.current) picker.current.value = ''
    }
  }

  return (
    <div className="editor">
      <div className="editor-bar">
        <span className="hint">Markdown</span>
        <span className="editor-tools">
          {allowUpload && (
            <>
              <input
                ref={picker}
                type="file"
                hidden
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) void upload(file)
                }}
              />
              <button
                type="button"
                className="linklike"
                disabled={uploading}
                onClick={() => picker.current?.click()}
              >
                {uploading ? '上传中…' : '附件'}
              </button>
            </>
          )}
          <button
            type="button"
            className="linklike"
            onClick={() => {
              if (showPreview) return setShowPreview(false)
              if (!value.trim()) return
              setShowPreview(true)
              preview.mutate(value)
            }}
          >
            {showPreview ? '继续编辑' : '预览'}
          </button>
        </span>
      </div>

      {showPreview && preview.data ? (
        <div className="preview post-body" ref={box}
             dangerouslySetInnerHTML={{ __html: preview.data.html }} />
      ) : (
        <div className="editor-input">
          {mention && candidates.length > 0 && (
            <ul className="mention-picker"
                style={{ top: caret.top + 22, left: caret.left }}>
              {candidates.map((u, i) => (
                <li key={u.id}>
                  <button
                    type="button"
                    className={i === active ? 'active' : ''}
                    onMouseEnter={() => setActive(i)}
                    onMouseDown={(e) => { e.preventDefault(); chooseMention(u.username) }}
                  >
                    <Avatar user={u} size={18} />
                    <span>
                      {u.nickname || u.username}
                      {u.nickname && <span className="muted"> @{u.username}</span>}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
          <textarea
            ref={area}
            value={value}
            rows={rows}
            placeholder={placeholder}
            onChange={(e) => {
              onChange(e.target.value)
              detectMention(e.target)
            }}
            onKeyDown={(e) => {
              if (!mention || candidates.length === 0) return
              if (e.key === 'ArrowDown') {
                e.preventDefault()
                setActive((i) => (i + 1) % candidates.length)
              } else if (e.key === 'ArrowUp') {
                e.preventDefault()
                setActive((i) => (i - 1 + candidates.length) % candidates.length)
              } else if (e.key === 'Enter' || e.key === 'Tab') {
                e.preventDefault()
                chooseMention(candidates[active].username)
              } else if (e.key === 'Escape') {
                setMention(null)
              }
            }}
          />
        </div>
      )}
      {preview.isPending && <p className="hint">渲染中…</p>}
      {error && <p className="event">{error}</p>}
      {preview.isError && <p className="event">预览失败</p>}
    </div>
  )
}
