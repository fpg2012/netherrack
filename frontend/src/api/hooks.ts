import { useQuery } from '@tanstack/react-query'
import { api } from './client'
import type {
  DiscussionBrief, DiscussionDetail, Me, Page, SearchHit, TagWithCount, TimelineItem,
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
