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
  is_public: boolean
  is_collapsed: boolean
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
  body_md: string | null
  is_legacy: boolean
  is_collapsed: boolean
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
  bio: string | null
  is_admin: boolean
}

export interface UserListItem {
  id: number
  username: string
  nickname: string | null
  avatar_path: string | null
  joined_at: string
  is_admin: boolean
  posts: number
  discussions: number
}

export interface Notification {
  id: number
  kind: 'reply' | 'quote' | 'best_answer' | 'mention' | 'system'
  discussion_id: number | null
  discussion_title: string | null
  post_id: number | null
  post_number: number | null
  title: string | null
  body: string | null
  actor: UserBrief | null
  read: boolean
  created_at: string
}

export interface UserProfile extends UserListItem {
  bio: string | null
}

export interface UserPost {
  post_id: number
  discussion_id: number
  discussion_title: string
  number: number
  created_at: string
  snippet: string
}

export interface Invite {
  id: number
  hint: string
  note: string | null
  status: 'active' | 'used' | 'expired' | 'revoked'
  created_at: string
  expires_at: string | null
  used_at: string | null
  used_by: string | null
  created_by: string | null
  revoked_at: string | null
}

export interface InviteCreated {
  id: number
  code: string
  expires_at: string | null
  note: string | null
}
