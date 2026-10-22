import { useEffect, useRef, useState } from 'react'
import { usePreview } from '../api/hooks'
import { renderMath } from '../lib/math'

interface Props {
  value: string
  onChange: (value: string) => void
  rows?: number
  placeholder?: string
}

export function MarkdownEditor({ value, onChange, rows = 10, placeholder }: Props) {
  const preview = usePreview()
  const box = useRef<HTMLDivElement>(null)
  const [showPreview, setShowPreview] = useState(false)

  useEffect(() => {
    if (showPreview && preview.data) renderMath(box.current)
  }, [showPreview, preview.data])

  return (
    <div className="editor">
      <div className="editor-bar">
        <span className="hint">Markdown</span>
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
      </div>
      {showPreview && preview.data ? (
        <div className="preview post-body" ref={box}
             dangerouslySetInnerHTML={{ __html: preview.data.html }} />
      ) : (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={rows}
          placeholder={placeholder}
        />
      )}
      {preview.isPending && <p className="hint">渲染中…</p>}
      {preview.isError && <p className="event">预览失败</p>}
    </div>
  )
}
