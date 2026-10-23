import { useEffect } from 'react'
import { Route, Routes, useLocation } from 'react-router-dom'
import { Footer } from './components/Footer'
import { Header } from './components/Header'
import { ToastHost } from './components/Toast'
import { NetherrackEgg } from './components/NetherrackEgg'
import { WidePage } from './components/WidePage'
import { useMeta } from './api/hooks'
import { setSiteTimezone } from './lib/format'
import { IndexPage } from './pages/IndexPage'
import { DiscussionPage } from './pages/DiscussionPage'
import { SearchPage } from './pages/SearchPage'
import { InvitesPage } from './pages/InvitesPage'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { NewDiscussionPage } from './pages/NewDiscussionPage'
import { UsersPage } from './pages/UsersPage'
import { UserPage } from './pages/UserPage'
import { NotificationsPage } from './pages/NotificationsPage'
import { SettingsPage } from './pages/SettingsPage'

export function App() {
  const meta = useMeta()
  const { pathname } = useLocation()
  const wide = pathname !== '/login' && pathname !== '/register'
  useEffect(() => { setSiteTimezone(meta.data?.timezone) }, [meta.data?.timezone])

  // 纹理从页脚分割线才开始出现：把页脚顶部位置写进 CSS 变量
  useEffect(() => {
    const update = () => {
      const footers = document.querySelectorAll<HTMLElement>('.site-footer, .side-footer')
      const footer = [...footers].find((el) => el.offsetParent !== null)
      if (!footer) return
      const footerTop = footer.getBoundingClientRect().top + window.scrollY
      // 正文列（含分页、回复框）彻底结束后才出现，避免盖住内容
      const main = document.querySelector<HTMLElement>('.thread-main, .index-main')
      const contentBottom = main ? main.getBoundingClientRect().bottom + window.scrollY : 0
      const top = Math.max(footerTop, contentBottom + 8)
      document.documentElement.style.setProperty('--tex-start', `${Math.round(top)}px`)
    }
    update()
    const ro = new ResizeObserver(update)
    ro.observe(document.body)
    window.addEventListener('resize', update)
    return () => {
      ro.disconnect()
      window.removeEventListener('resize', update)
    }
  }, [pathname])

  return (
    <div className={wide ? 'shell wide' : 'shell'}>
      <Header />
      <ToastHost />
      <NetherrackEgg />
      <main className="page">
        <Routes>
          <Route path="/" element={<IndexPage />} />
          <Route path="/d/:id" element={<DiscussionPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route element={<WidePage />}>
            <Route path="/search" element={<SearchPage />} />
            <Route path="/new" element={<NewDiscussionPage />} />
            <Route path="/users" element={<UsersPage />} />
            <Route path="/u/:id" element={<UserPage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/invites" element={<InvitesPage />} />
            <Route path="*" element={<p>页面不存在。</p>} />
          </Route>
        </Routes>
      </main>
      <Footer />
    </div>
  )
}
