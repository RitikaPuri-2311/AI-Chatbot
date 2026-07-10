export type Role = 'user' | 'assistant'

export interface Message {
  id: string
  role: Role
  content: string
  createdAt: string
  sources?: Source[]
}

export interface User {
  id: string
  email: string
  username: string
}

export interface AuthResponse {
  accessToken: string
  user: User
}

export interface ChatSession {
  id: string
  title: string
  createdAt: string
}

export interface Document {
  id: string
  filename: string
  status: 'processing' | 'indexed' | 'failed'
  chunk_count: number
  page_count: number
  created_at: string
}

export interface Source {
  source: string
  page: number
  text_snippet: string
  similarity?: number
}

export interface QueryResult {
  answer: string
  sources: Source[]
  tool_calls?: unknown[]
  iterations?: number
}

export interface ConversationOverview {
  total_conversations: number
  average_duration: string
  average_messages: number
  most_used_persona: string
}

export interface TopicCount {
  topic: string
  count: number
}

export interface TopicAnalytics {
  topics: TopicCount[]
}

export interface SentimentAnalytics {
  positive: number
  neutral: number
  negative: number
}