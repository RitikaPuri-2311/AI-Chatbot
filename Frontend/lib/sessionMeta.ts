import { getUser } from '@/lib/auth'

const PIN_KEY = 'chatbot_pinned_sessions'

function storageKey(): string {
  const user = getUser()
  return user ? `${PIN_KEY}_${user.id}` : PIN_KEY
}

export function getPinnedSessionIds(): string[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = localStorage.getItem(storageKey())
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

export function setPinnedSessionIds(ids: string[]): void {
  localStorage.setItem(storageKey(), JSON.stringify(ids))
}

export function togglePinSession(sessionId: string): boolean {
  const pinned = getPinnedSessionIds()
  const isPinned = pinned.includes(sessionId)
  const next = isPinned
    ? pinned.filter(id => id !== sessionId)
    : [sessionId, ...pinned]
  setPinnedSessionIds(next)
  return !isPinned
}

export function isSessionPinned(sessionId: string): boolean {
  return getPinnedSessionIds().includes(sessionId)
}
