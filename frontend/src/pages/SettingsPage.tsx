import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useChangePassword, useLogout, useMe, useUpdateProfile, useUploadAvatar } from '../api/hooks'
import { Avatar } from '../components/Avatar'

function Message({ tone, children }: { tone: 'ok' | 'err'; children: string }) {
  return <p className={tone === 'ok' ? 'msg ok' : 'msg err'}>{children}</p>
}

export function SettingsPage() {
  const me = useMe()
  const profile = useUpdateProfile(me.data?.id)
  const avatar = useUploadAvatar(me.data?.id)
  const password = useChangePassword()
  const logout = useLogout()

  const [nickname, setNickname] = useState('')
  const [bio, setBio] = useState('')
  const [saved, setSaved] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirm, setConfirm] = useState('')
  const [pwdDone, setPwdDone] = useState(false)
  const fileInput = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (me.data) {
      setNickname(me.data.nickname ?? '')
      setBio(me.data.bio ?? '')
    }
  }, [me.data])

  if (!me.data) return <p className="muted"><Link to="/login">登录</Link> 后修改设置。</p>

  return (
    <>
      <h1>设置</h1>

      <section className="settings">
        <h2>个人资料</h2>
        <p className="muted small">昵称留空则显示用户名 {me.data.username}。</p>
        <label>
          <span>昵称</span>
          <input className="inline" value={nickname} maxLength={32}
                 onChange={(e) => { setNickname(e.target.value); setSaved(false) }} />
        </label>
        <label>
          <span>自我介绍</span>
          <textarea className="inline" rows={4} value={bio} maxLength={500}
                    placeholder="支持换行，会显示在个人主页"
                    onChange={(e) => { setBio(e.target.value); setSaved(false) }} />
        </label>
        <div className="settings-actions">
          <button type="button" className="button" disabled={profile.isPending}
                  onClick={() => profile.mutate({ nickname, bio }, {
                    onSuccess: () => setSaved(true),
                  })}>
            {profile.isPending ? '保存中…' : '保存'}
          </button>
          {saved && <Message tone="ok">已保存</Message>}
          {profile.isError && <Message tone="err">{profile.error.message}</Message>}
        </div>
      </section>

      <section className="settings">
        <h2>头像</h2>
        <div className="avatar-row">
          <Avatar user={me.data} size={64} />
          <div>
            <input ref={fileInput} type="file" accept="image/png,image/jpeg,image/gif,image/webp"
                   onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
            <p className="muted small">PNG / JPEG / GIF / WebP，不超过 2 MB。</p>
            <div className="settings-actions">
              <button type="button" className="button" disabled={!file || avatar.isPending}
                      onClick={() => {
                        if (!file) return
                        const form = new FormData()
                        form.append('file', file)
                        avatar.mutate(form, {
                          onSuccess: () => {
                            setFile(null)
                            if (fileInput.current) fileInput.current.value = ''
                          },
                        })
                      }}>
                {avatar.isPending ? '上传中…' : '上传'}
              </button>
              {avatar.isError && <Message tone="err">{avatar.error.message}</Message>}
            </div>
          </div>
        </div>
      </section>

      <section className="settings">
        <h2>密码</h2>
        {pwdDone ? (
          <p className="muted">密码已修改，请重新登录。<Link to="/login">去登录</Link></p>
        ) : (
          <>
            <label>
              <span>当前密码</span>
              <input className="inline" type="password" autoComplete="current-password"
                     value={current} onChange={(e) => setCurrent(e.target.value)} />
            </label>
            <label>
              <span>新密码</span>
              <input className="inline" type="password" autoComplete="new-password"
                     value={next} onChange={(e) => setNext(e.target.value)} />
            </label>
            <label>
              <span>确认新密码</span>
              <input className="inline" type="password" autoComplete="new-password"
                     value={confirm} onChange={(e) => setConfirm(e.target.value)} />
            </label>
            <div className="settings-actions">
              <button type="button" className="button" disabled={password.isPending}
                      onClick={() => {
                        if (next.length < 8) return
                        if (next !== confirm) return
                        password.mutate({ current_password: current, new_password: next }, {
                          onSuccess: () => {
                            setPwdDone(true)
                            setTimeout(() => logout.mutate(), 1500)
                          },
                        })
                      }}>
                {password.isPending ? '提交中…' : '修改密码'}
              </button>
              {next.length > 0 && next.length < 8 && <Message tone="err">新密码至少 8 位</Message>}
              {confirm.length > 0 && next !== confirm && <Message tone="err">两次输入不一致</Message>}
              {password.isError && <Message tone="err">{password.error.message}</Message>}
            </div>
          </>
        )}
      </section>
    </>
  )
}
