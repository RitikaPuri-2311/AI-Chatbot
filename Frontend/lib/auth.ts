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

const API_URL = 'http://localhost:8000'

export async function login(
  email: string,
  password: string
): Promise<AuthResponse> {
  const res = await fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  })
  if (!res.ok) {
    const error = await res.json()
    throw new Error(error.detail ?? 'Login failed')
  }
  return res.json()
}

export async function register(
  email: string,
  username: string,
  password: string
): Promise<AuthResponse> {
  const res = await fetch(`${API_URL}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, username, password })
  })
  if (!res.ok) {
    const error = await res.json()
    throw new Error(error.detail ?? 'Registration failed')
  }
  return res.json()
}

export function logout(): void {
  clearAuth()
  window.location.href = '/login'
}