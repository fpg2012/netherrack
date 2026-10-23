import { useEffect } from 'react'
import { Route, Routes } from 'react-router-dom'
import { Footer } from './components/Footer'
import { Header } from './components/Header'
import { ToastHost } from './components/Toast'
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
  useEffect(() => { setSiteTimezone(meta.data?.timezone) }, [meta.data?.timezone])

  return (
    <>
      <Header />
      <ToastHost />
      <main className="page">
        <Routes>
        <Route path="/" element={<IndexPage />} />
        <Route path="/d/:id" element={<DiscussionPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/invites" element={<InvitesPage />} />
        <Route path="/new" element={<NewDiscussionPage />} />
        <Route path="/users" element={<UsersPage />} />
          <Route path="/u/:id" element={<UserPage />} />
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<p>页面不存在。</p>} />
        </Routes>
      </main>
      <Footer />
    </>
  )
}
