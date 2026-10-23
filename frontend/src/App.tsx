import { useEffect } from 'react'
import { Route, Routes, useLocation } from 'react-router-dom'
import { Footer } from './components/Footer'
import { Header } from './components/Header'
import { ToastHost } from './components/Toast'
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

  return (
    <div className={wide ? 'shell wide' : 'shell'}>
      <Header />
      <ToastHost />
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
