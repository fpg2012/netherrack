import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './client'
import type {
  DiscussionBrief, DiscussionDetail, Me, Notification, Page, Post, SearchHit, TagWithCount,
  TimelineItem, UserListItem, UserPost, UserProfile,
} from '../types'

export function useDiscussions(params: { page: number; tag?: string | null }) {
  const search = new URLSearchParams({ page: String(params.page) })
  if (params.tag) search.set('tag', params.tag)
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
    queryFn: () => api.get<{ discussions: number; posts: number; users: number }>('/meta'),
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
    mutationFn: (body: { body_md: string; quote_post_id?: number | null }) =>
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

export function useEditDiscussion(discussionId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: {
      title?: string
      is_sticky?: boolean
      is_locked?: boolean
      is_public?: boolean
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
    refetchInterval: 60_000,
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
