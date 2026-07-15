import type {
  Message,
  ChatSession,
  SupportRequestPayload,
  SupportRequestResponse,
} from '@/types'
import { getToken, getUser } from '@/lib/auth'
import toast from 'react-hot-toast'

const API_URL = 'http://localhost:8000'

export function getSessionId(): string {
  const user = getUser()
  if (!user) return 'session-001'
  return `session-${user.id}`
}

export async function getSessions(): Promise<ChatSession[]> {
  try {
    const token = getToken()
    if (!token) return []
    const res = await fetch(`${API_URL}/api/chat/sessions`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (!res.ok) return []
    const data = await res.json()
    return data.sessions
  } catch {
    return []
  }
}

export async function createSession(): Promise<ChatSession | null> {
  try {
    const token = getToken()
    if (!token) return null
    const res = await fetch(`${API_URL}/api/chat/sessions`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

export async function renameSession(
  sessionId: string,
  title: string,
): Promise<ChatSession | null> {
  try {
    const token = getToken()
    if (!token) return null
    const res = await fetch(
      `${API_URL}/api/chat/sessions/${sessionId}`,
      {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title }),
      },
    )
    if (!res.ok) return null
    const data = await res.json()
    return {
      id: data.id,
      title: data.title,
      createdAt: '',
    }
  } catch {
    return null
  }
}

export async function deleteSession(sessionId: string): Promise<boolean> {
  try {
    const token = getToken()
    if (!token) return false
    const res = await fetch(
      `${API_URL}/api/chat/sessions/${sessionId}`,
      {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      }
    )
    if (res.ok) {
      toast.success('Chat deleted')
    }
    return res.ok
  } catch {
    return false
  }
}

export async function sendMessage(
  content: string,
  sessionId: string,
  persona: string = 'default', 
  onChunk: (chunk: string) => void
): Promise<void> {
  const token = getToken()
  if (!token) throw new Error('Not authenticated')

  const response = await fetch(`${API_URL}/api/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      message: content,
      session_id: sessionId,
      persona: persona     
    })
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    const detail = error.detail ?? 'Chat request failed'

    // Check for rate limit specifically
    if (
      response.status === 429 ||
      detail.includes('429') ||
      detail.includes('quota') ||
      detail.includes('rate')
    ) {
      toast.error(
        '⚠️ Free tier limit reached! Gemini allows 15 requests/min. Please wait a moment.',
        { duration: 8000 }
      )
    } else if (response.status === 401) {
      toast.error('Session expired. Please login again.')
    } else {
      toast.error(`Error: ${detail}`)
    }

    throw new Error(detail)
  }

  if (!response.body) throw new Error('No response body')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const chunk = line.slice(6)
          if (chunk === '[DONE]') return
          if (chunk.startsWith('[ERROR]')) {
            const errMsg = chunk.replace('[ERROR] ', '')
            // Rate limit check inside stream
            if (
              errMsg.includes('429') ||
              errMsg.includes('quota') ||
              errMsg.includes('rate')
            ) {
              toast.error(
                '⚠️ Free tier limit reached! Please wait 60 seconds before sending another message.',
                { duration: 8000 }
              )
            } else {
              toast.error(`AI Error: ${errMsg}`)
            }
            throw new Error(errMsg)
          }
          if (chunk.trim()) onChunk(chunk)
        }
      }
    }
  } catch (err) {
    console.log('Stream ended:', err)
  } finally {
    reader.releaseLock()
  }
}

export async function getMessages(
  sessionId: string
): Promise<Message[]> {
  try {
    const token = getToken()
    if (!token) return []
    const res = await fetch(
      `${API_URL}/api/chat/history/${sessionId}`,
      {
        headers: { 'Authorization': `Bearer ${token}` }
      }
    )
    if (!res.ok) return []
    const data = await res.json()
    return data.messages.map((m: Message) => ({
      ...m,
      createdAt: m.createdAt || new Date().toISOString()
    }))
  } catch {
    return []
  }
}
export async function uploadDocument(file: File): Promise<unknown> {
  const formData = new FormData()
  formData.append('file', file)

  const res = await fetch(`${API_URL}/api/documents/upload`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${getToken()}` },
    body: formData
  })

  if (!res.ok) {
    const error = await res.json().catch(() => ({}))
    throw new Error(error.detail ?? 'Upload failed')
  }
  return res.json()
}

export async function getDocuments(): Promise<unknown[]> {
  try {
    const res = await fetch(`${API_URL}/api/documents/`, {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    })
    if (!res.ok) return []
    const data = await res.json()
    return data.documents
  } catch {
    return []
  }
}

export async function queryDocuments(
  question: string,
  documentId: string | null,
  sessionId?: string,
  options?: { faqMode?: boolean; weatherMode?: boolean }
): Promise<{ answer: string; sources: unknown[] }> {
  const body: Record<string, unknown> = {
    question,
    session_id: sessionId,
    stream: false,
  }
  if (documentId) {
    body.document_id = documentId
  }
  if (options?.faqMode) {
    body.faq_mode = true
  }
  if (options?.weatherMode) {
    body.weather_mode = true
  }

  const res = await fetch(`${API_URL}/api/documents/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}`
    },
    body: JSON.stringify(body)
  })

  if (!res.ok) {
    const error = await res.json().catch(() => ({}))
    throw new Error(error.detail ?? 'Query failed')
  }
  return res.json()
}

export async function deleteDocument(documentId: string): Promise<boolean> {
  try {
    const res = await fetch(
      `${API_URL}/api/documents/${documentId}`,
      {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${getToken()}` }
      }
    )
    return res.ok
  } catch {
    return false
  }
}

export async function submitSupportRequest(
  payload: SupportRequestPayload,
): Promise<SupportRequestResponse> {
  const token = getToken()
  if (!token) throw new Error('Not authenticated')

  const res = await fetch(`${API_URL}/api/jira/create`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  })

  if (!res.ok) {
    const error = await res.json().catch(() => ({}))
    const detail = (error as { detail?: string }).detail

    if (res.status >= 500) {
      throw new Error('The server is currently unavailable. Please try again later.')
    }

    throw new Error(detail ?? 'Unable to submit your request. Please try again.')
  }

  return res.json()
}