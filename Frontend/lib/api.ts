import type { Message } from '@/types'
import { getToken } from '@/lib/auth'

const API_URL = 'http://localhost:8000'
export const MOCK_SESSION_ID = 'session-001'

export async function sendMessage(content: string): Promise<Message> {
  const res = await fetch(`${API_URL}/api/chat/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}`
    },
    body: JSON.stringify({
      message: content,
      session_id: MOCK_SESSION_ID
    })
  })
  if (!res.ok) {
    const error = await res.json()
    throw new Error(error.detail ?? 'Chat failed')
  }
  const data = await res.json()
  return {
    id: data.id,
    role: 'assistant',
    content: data.content,
    createdAt: new Date().toISOString()
  }
}

export async function getMessages(): Promise<Message[]> {
  const res = await fetch(
    `${API_URL}/api/chat/history/${MOCK_SESSION_ID}`,
    {
      headers: {
        'Authorization': `Bearer ${getToken()}`
      }
    }
  )
  if (!res.ok) return []
  const data = await res.json()
  return data.messages.map((m: Message) => ({
    ...m,
    createdAt: m.createdAt || new Date().toISOString()
  }))
}