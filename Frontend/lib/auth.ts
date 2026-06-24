import type { User, AuthResponse } from '@/types'

const TOKEN_KEY = 'chatbot_token'
const USER_KEY = 'chatbot_user'

export function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(TOKEN_KEY)
}

export function getUser(): User | null {
  if (typeof window === 'undefined') return null
  const raw = localStorage.getItem(USER_KEY)
  return raw ? JSON.parse(raw) : null
}

export function saveAuth(token: string, user: User): void {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearAuth(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export async function login(
  email: string,
  password: string
): Promise<AuthResponse> {
  await new Promise(r => setTimeout(r, 800))
  if (email === 'test@test.com' && password === 'password123') {
    return {
      accessToken: 'mock-jwt-token-abc123',
      user: { id: '1', email, username: 'testuser' }
    }
  }
  throw new Error('Invalid email or password')
}

export async function register(
  email: string,
  username: string,
  password: string
): Promise<AuthResponse> {
  await new Promise(r => setTimeout(r, 800))
  if (!email || !username || !password) {
    throw new Error('All fields are required')
  }
  return {
    accessToken: 'mock-jwt-token-abc123',
    user: { id: '1', email, username }
  }
}

export function logout(): void {
  clearAuth()
  window.location.href = '/login'
}