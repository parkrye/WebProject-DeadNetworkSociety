export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  total_pages: number
}

export interface User {
  id: string
  nickname: string
  is_agent: boolean
  created_at: string
  updated_at: string
}

export interface Post {
  id: string
  author_id: string
  title: string
  content: string
  created_at: string
  updated_at: string
}

export interface PostEnriched {
  id: string
  author_id: string
  author_nickname: string
  title: string
  content: string
  like_count: number
  dislike_count: number
  comment_count: number
  created_at: string
  updated_at: string
}

export interface Comment {
  id: string
  post_id: string
  parent_id: string | null
  author_id: string
  content: string
  depth: number
  created_at: string
  updated_at: string
}

export interface ReactionCounts {
  target_type: string
  target_id: string
  like: number
  dislike: number
}

export interface AgentProfile {
  id: string
  user_id: string
  persona_file: string
  is_active: boolean
  last_action_at: string | null
  created_at: string
  updated_at: string
}
