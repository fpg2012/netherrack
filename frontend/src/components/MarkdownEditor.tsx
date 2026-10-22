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
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
        placeholder={placeholder}
      />
      <div className="editor-bar">
        <button
          type="button"
          onClick={() => {
            if (!value.trim()) return
            setShowPreview(true)
            preview.mutate(value)
          }}
        >
          预览
        </button>
        {preview.isPending && <span className="muted">渲染中…</span>}
        {preview.isError && <span className="event">预览失败</span>}
      </div>
      {showPreview && preview.data && (
        <div className="preview post-body" ref={box}
             dangerouslySetInnerHTML={{ __html: preview.data.html }} />
      )}
    </div>
  )
}
