import { useEffect, useRef, useState } from 'react'
import { usePreview } from '../api/hooks'
import { api } from '../api/client'
import { renderMath } from '../lib/math'

interface Props {
  value: string
  onChange: (value: string) => void
  rows?: number
  placeholder?: string
  allowUpload?: boolean
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
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (showPreview && preview.data) renderMath(box.current)
  }, [showPreview, preview.data])

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
        <textarea
          ref={area}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={rows}
          placeholder={placeholder}
        />
      )}
      {preview.isPending && <p className="hint">渲染中…</p>}
      {error && <p className="event">{error}</p>}
      {preview.isError && <p className="event">预览失败</p>}
    </div>
  )
}
