import { useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './client'
import type {
  DiscussionBrief, DiscussionDetail, Invite, InviteCreated, Me, Notification, Page, Post,
  SearchHit, TagWithCount,
  TimelineItem, UserBrief, UserListItem, UserPost, UserProfile,
} from '../types'

export function useDiscussions(params: { page: number; tag?: string | null; untagged?: boolean }) {
  const search = new URLSearchParams({ page: String(params.page) })
  if (params.untagged) search.set('untagged', '1')
  else if (params.tag) search.set('tag', params.tag)
  return useQuery({
    queryKey: ['discussions', params],
    queryFn: () => api.get<Page<DiscussionBrief>>(`/discussions?${search}`),
    placeholderData: (prev) => prev,
  })
}

export function useTags() {
  return useQuery({ queryKey: ['tags'], queryFn: () => api.get<TagWithCount[]>('/tags') })
}

export function useDiscussion(id: number) {
  return useQuery({
    queryKey: ['discussion', id],
    queryFn: () => api.get<DiscussionDetail>(`/discussions/${id}`),
  })
}

export function useTimeline(id: number, page: number) {
  return useQuery({
    queryKey: ['timeline', id, page],
    queryFn: () => api.get<Page<TimelineItem>>(`/discussions/${id}/timeline?page=${page}`),
    placeholderData: (prev) => prev,
  })
}

export function useSearch(q: string, page: number) {
  return useQuery({
    queryKey: ['search', q, page],
    queryFn: () => api.get<Page<SearchHit>>(`/search?q=${encodeURIComponent(q)}&page=${page}`),
    enabled: q.length > 0,
    placeholderData: (prev) => prev,
  })
}

export function useMeta() {
  return useQuery({
    queryKey: ['meta'],
    queryFn: () => api.get<{
      discussions: number; posts: number; users: number; untagged: number; timezone: string
    }>('/meta'),
    staleTime: 5 * 60_000,
  })
}

export function useMe() {
  return useQuery({
    queryKey: ['me'],
    queryFn: () => api.get<Me>('/auth/me'),
    retry: false,
  })
}


// ---------------------------------------------------------------- 写操作

export function useCreateDiscussion() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { title: string; body_md: string; tags: string[] }) =>
      api.post<DiscussionDetail>('/discussions', body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['discussions'] }),
  })
}

export function useReply(discussionId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: {
      body_md: string
      quote_post_id?: number | null
      reply_to_post_id?: number | null
    }) =>
      api.post<Post>(`/discussions/${discussionId}/posts`, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['timeline', discussionId] })
      qc.invalidateQueries({ queryKey: ['discussions'] })
    },
  })
}

export function useEditPost(discussionId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body_md }: { id: number; body_md: string }) =>
      api.patch<Post>(`/posts/${id}`, { body_md }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['timeline', discussionId] }),
  })
}

export function useCollapsePost(discussionId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, is_collapsed }: { id: number; is_collapsed: boolean }) =>
      api.patch<Post>(`/posts/${id}/collapse`, { is_collapsed }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['timeline', discussionId] }),
  })
}

export function useEditDiscussion(discussionId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: {
      title?: string
      is_sticky?: boolean
      is_locked?: boolean
      is_public?: boolean
      is_collapsed?: boolean
      tags?: string[]
      best_answer_post_id?: number
    }) => api.patch<DiscussionDetail>(`/discussions/${discussionId}`, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['discussion', discussionId] })
      qc.invalidateQueries({ queryKey: ['timeline', discussionId] })
      qc.invalidateQueries({ queryKey: ['discussions'] })
    },
  })
}

export function usePreview() {
  return useMutation({
    mutationFn: (body_md: string) => api.post<{ html: string }>('/preview', { body_md }),
  })
}

export function useMentionable(discussionId: number) {
  return useQuery({
    queryKey: ['mentionable', discussionId],
    queryFn: () => api.get<UserBrief[]>(`/discussions/${discussionId}/mentionable`),
    staleTime: 60_000,
  })
}

export function useAllUsers() {
  return useQuery({
    queryKey: ['users', 'all'],
    queryFn: () => api.get<Page<UserListItem>>('/users?per_page=100'),
    staleTime: 5 * 60_000,
  })
}

export function useUsers(page: number, q: string) {
  const search = new URLSearchParams({ page: String(page) })
  if (q) search.set('q', q)
  return useQuery({
    queryKey: ['users', page, q],
    queryFn: () => api.get<Page<UserListItem>>(`/users?${search}`),
    placeholderData: (prev) => prev,
  })
}

export function useLogout() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.post<void>('/auth/logout'),
    onSettled: () => {
      qc.removeQueries({ queryKey: ['me'] })
      qc.invalidateQueries()
    },
  })
}


// ---------------------------------------------------------------- 通知与用户

export function useNotifications(page: number) {
  return useQuery({
    queryKey: ['notifications', page],
    queryFn: () => api.get<Page<Notification>>(`/notifications?page=${page}`),
    placeholderData: (prev) => prev,
  })
}

export function useUnreadCount() {
  return useQuery({
    queryKey: ['notifications', 'unread'],
    queryFn: () => api.get<{ count: number }>('/notifications/unread'),
    // SSE 是主要通道，这里只做兜底（SSE 断线时最长 2 分钟也能同步）
    refetchInterval: 120_000,
  })
}

/** 订阅 SSE：有新通知时让未读数和列表失效。 */
export function useNotificationStream(enabled: boolean) {
  const qc = useQueryClient()
  useEffect(() => {
    if (!enabled) return
    const source = new EventSource('/api/v1/stream')
    source.addEventListener('notify', () => {
      qc.invalidateQueries({ queryKey: ['notifications'] })
    })
    return () => source.close()
  }, [enabled, qc])
}

export function useBroadcast() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { title: string; body: string }) =>
      api.post<{ sent: number }>('/notifications/broadcast', body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  })
}

export function useMarkRead() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.post<void>(`/notifications/${id}/read`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  })
}

export function useReadAll() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.post<{ updated: number }>('/notifications/read-all'),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  })
}

export function useUser(id: number) {
  return useQuery({
    queryKey: ['user', id],
    queryFn: () => api.get<UserProfile>(`/users/${id}`),
  })
}

export function useUserDiscussions(id: number, page: number) {
  return useQuery({
    queryKey: ['user', id, 'discussions', page],
    queryFn: () => api.get<Page<DiscussionBrief>>(`/users/${id}/discussions?page=${page}`),
  })
}

export function useUserPosts(id: number, page: number) {
  return useQuery({
    queryKey: ['user', id, 'posts', page],
    queryFn: () => api.get<Page<UserPost>>(`/users/${id}/posts?page=${page}`),
  })
}


// ---------------------------------------------------------------- 设置

export function useUpdateProfile(id: number | undefined) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { nickname: string; bio: string }) =>
      api.patch<UserProfile>('/users/me', body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['me'] })
      if (id) qc.invalidateQueries({ queryKey: ['user', id] })
    },
  })
}

export function useUploadAvatar(id: number | undefined) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (form: FormData) => api.postForm<UserProfile>('/users/me/avatar', form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['me'] })
      if (id) qc.invalidateQueries({ queryKey: ['user', id] })
    },
  })
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (body: { current_password: string; new_password: string }) =>
      api.post<void>('/users/me/password', body),
  })
}

export function useInvites() {
  return useQuery({
    queryKey: ['invites'],
    queryFn: () => api.get<Invite[]>('/invites'),
  })
}

export function useCreateInvite() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { expires_in_days: number; note?: string }) =>
      api.post<InviteCreated>('/invites', body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['invites'] }),
  })
}

export function useRevokeInvite() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.del<void>(`/invites/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['invites'] }),
  })
}
