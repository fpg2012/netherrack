import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useCreateInvite, useInvites, useMe, useRevokeInvite } from '../api/hooks'
import { toast } from '../components/Toast'
import { datetime } from '../lib/format'
import type { Invite, InviteCreated } from '../types'

const STATUS: Record<Invite['status'], { label: string; cls: string }> = {
  active: { label: '可用', cls: 'status-active' },
  used: { label: '已使用', cls: 'status-muted' },
  expired: { label: '已过期', cls: 'status-muted' },
  revoked: { label: '已撤销', cls: 'status-void' },
}

export function InvitesPage() {
  const me = useMe()
  const invites = useInvites()
  const create = useCreateInvite()
  const revoke = useRevokeInvite()
  const [created, setCreated] = useState<InviteCreated | null>(null)
  const [copied, setCopied] = useState(false)
  const [note, setNote] = useState('')
  const [days, setDays] = useState(7)

  if (me.data && !me.data.is_admin) {
    return <p>只有管理员可以管理邀请码。<Link to="/">返回首页</Link></p>
  }

  const rows = invites.data ?? []
  const active = rows.filter((i) => i.status === 'active').length

  const copy = async () => {
    if (!created) return
    try {
      await navigator.clipboard.writeText(created.code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      /* 非 HTTPS 或权限被拒时还可以手动选中复制 */
    }
  }

  return (
    <>
      <h1>邀请码</h1>

      <section className="invite-panel">
        <h2>生成新邀请码</h2>
        <form
          className="inline-form"
          onSubmit={(e) => {
            e.preventDefault()
            create.mutate(
              { expires_in_days: days, note: note.trim() || undefined },
              {
                onSuccess: (data) => {
                  setCreated(data)
                  setCopied(false)
                  setNote('')
                  toast('邀请码已生成，明文只显示这一次')
                },
              },
            )
          }}
        >
          <input value={note} onChange={(e) => setNote(e.target.value)}
            placeholder="备注（给谁用的，可选）" maxLength={100} />
          <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
            <option value={1}>1 天有效</option>
            <option value={7}>7 天有效</option>
            <option value={30}>30 天有效</option>
            <option value={90}>90 天有效</option>
          </select>
          <button type="submit" disabled={create.isPending}>
            {create.isPending ? '生成中…' : '生成'}
          </button>
        </form>
        {create.isError && <p className="event">{create.error.message}</p>}
      </section>

      {created && (
        <section className="invite-created">
          <h2>新邀请码</h2>
          <div className="code-row">
            <code>{created.code}</code>
            <button type="button" onClick={copy}>{copied ? '已复制' : '复制'}</button>
          </div>
          <p className="muted">
            关闭后不再显示。
            {created.expires_at ? ` ${datetime(created.expires_at)} 到期。` : ' 长期有效。'}
            {created.note ? ` 备注：${created.note}` : ''}
          </p>
        </section>
      )}

      <div className="invite-list-head">
        <span className="label">全部邀请码</span>
        <span className="muted">共 {rows.length} 个 · 可用 {active} 个</span>
      </div>

      <div className="table-wrap">
        <table className="tbl invites">
          <thead>
            <tr>
              <th>邀请码</th>
              <th>备注</th>
              <th>状态</th>
              <th>创建</th>
              <th>到期</th>
              <th>使用者</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.map((invite) => {
              const status = STATUS[invite.status]
              return (
                <tr key={invite.id}>
                  <td><code>••••-{invite.hint}</code></td>
                  <td className="muted">{invite.note || '—'}</td>
                  <td><span className={`status ${status.cls}`}>{status.label}</span></td>
                  <td className="muted nowrap">{datetime(invite.created_at)}</td>
                  <td className="muted nowrap">
                    {invite.expires_at ? datetime(invite.expires_at) : '长期'}
                  </td>
                  <td className="muted">{invite.used_by || '—'}</td>
                  <td className="actions">
                    {invite.status === 'active' && (
                      <button
                        type="button"
                        className="linkish"
                        disabled={revoke.isPending}
                        onClick={() => {
                          if (confirm(`撤销邀请码 ••••-${invite.hint}？`)) revoke.mutate(invite.id)
                        }}
                      >
                        撤销
                      </button>
                    )}
                  </td>
                </tr>
              )
            })}
            {rows.length === 0 && (
              <tr>
                <td colSpan={7} className="empty">还没有邀请码。</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {revoke.isError && <p className="event">{revoke.error.message}</p>}
    </>
  )
}
