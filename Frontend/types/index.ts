export type Role = 'user' | 'assistant'

export interface Message {
  id: string
  role: Role
  content: string
  createdAt: string
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