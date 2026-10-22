import { Route, Routes } from 'react-router-dom'
import { Header } from './components/Header'
import { IndexPage } from './pages/IndexPage'
import { DiscussionPage } from './pages/DiscussionPage'
import { SearchPage } from './pages/SearchPage'
import { LoginPage } from './pages/LoginPage'
import { NewDiscussionPage } from './pages/NewDiscussionPage'
import { UsersPage } from './pages/UsersPage'
import { UserPage } from './pages/UserPage'
import { NotificationsPage } from './pages/NotificationsPage'

export function App() {
  return (
    <>
      <Header />
      <main className="page">
        <Routes>
        <Route path="/" element={<IndexPage />} />
        <Route path="/d/:id" element={<DiscussionPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/new" element={<NewDiscussionPage />} />
        <Route path="/users" element={<UsersPage />} />
          <Route path="/u/:id" element={<UserPage />} />
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="*" element={<p>页面不存在。</p>} />
        </Routes>
      </main>
    </>
  )
}
