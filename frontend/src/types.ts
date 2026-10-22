export interface UserBrief {
  id: number
  username: string
  nickname: string | null
  avatar_path: string | null
}

export interface Tag {
  id: number
  name: string
  slug: string
  color: string | null
  is_qna: boolean
}

export interface TagWithCount extends Tag {
  count: number
}

export interface DiscussionBrief {
  id: number
  title: string
  slug: string | null
  is_sticky: boolean
  is_locked: boolean
  post_count: number
  created_at: string
  last_posted_at: string | null
  author: UserBrief | null
  tags: Tag[]
}

export interface DiscussionDetail extends DiscussionBrief {
  best_answer_post_id: number | null
}

export interface Post {
  id: number
  number: number
  created_at: string
  edited_at: string | null
  body_html: string
  is_legacy: boolean
  author: UserBrief | null
}

export interface TimelineEvent {
  id: number
  kind: string
  text: string
  created_at: string
}

export interface TimelineItem {
  type: 'post' | 'event'
  id: number
  created_at: string
  post: Post | null
  event: TimelineEvent | null
}

export interface SearchHit {
  post_id: number
  discussion_id: number
  discussion_title: string
  number: number
  created_at: string
  author: UserBrief | null
  snippet: string
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  pages: number
  per_page: number
}

export interface Me {
  id: number
  username: string
  nickname: string | null
  avatar_path: string | null
  is_admin: boolean
}
