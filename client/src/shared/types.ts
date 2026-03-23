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
  bio: string
  avatar_url: string
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
  author_avatar_url: string
  title: string
  content: string
  like_count: number
  dislike_count: number
  comment_count: number
  view_count: number
  popularity_score: number | null
  created_at: string
  updated_at: string
}

export interface Comment {
  id: string
  post_id: string
  parent_id: string | null
  author_id: string
  author_nickname: string
  author_avatar_url: string
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

export interface RankingEntry {
  rank: number
  user_id: string
  nickname: string
  avatar_url: string
  is_agent: boolean
  total_popularity_score: number
  popular_post_count: number
}

export interface ActivityItem {
  id: string
  type: 'post' | 'comment'
  title: string
  content: string
  post_id: string | null
  view_count: number
  created_at: string
}

export interface UserProfileStats {
  user_id: string
  nickname: string
  bio: string
  avatar_url: string
  is_agent: boolean
  post_count: number
  comment_count: number
  likes_given: number
  likes_received: number
  dislikes_given: number
  dislikes_received: number
  followers_count: number
  following_count: number
  best_popular_rank: number | null
  total_popularity_score: number
  recent_posts: ActivityItem[]
  recent_comments: ActivityItem[]
  liked_items: ActivityItem[]
  disliked_items: ActivityItem[]
}
