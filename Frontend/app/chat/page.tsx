'use client'

import { useState, useEffect, useCallback } from 'react'
import { MessageSquare, ChevronDown } from 'lucide-react'
import AppShell from '@/components/layout/AppShell'
import PageHeader from '@/components/layout/PageHeader'
import ChatHistorySidebar from '@/components/chat/ChatHistorySidebar'
import ChatWindow from '@/components/chat/ChatWindow'
import MessageInput from '@/components/chat/MessageInput'
import WeatherQuickChips from '@/components/weather/WeatherQuickChips'
import { WEATHER_LOADING_MESSAGE } from '@/components/weather/weatherConfig'
import { AI_SUGGESTED_PROMPTS, PERSONA_OPTIONS } from '@/components/chat/chatConfig'
import { useAuth } from '@/hooks/useAuth'
import {
  sendMessage,
  getMessages,
  getSessions,
  createSession,
  deleteSession,
  renameSession,
  queryDocuments,
} from '@/lib/api'
import toast from 'react-hot-toast'
import type { Message, ChatSession, Source } from '@/types'

export default function ChatPage() {
  const { user } = useAuth()
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingMessages, setIsLoadingMessages] = useState(true)
  const [isLoadingSessions, setIsLoadingSessions] = useState(true)
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [activeSessionId, setActiveSessionId] = useState('')
  const [persona, setPersona] = useState('default')
  const [streamingId, setStreamingId] = useState<string | null>(null)

  const isWeatherMode = persona === 'weather'
  const activeSession = sessions.find(s => s.id === activeSessionId)

  async function loadSessions() {
    setIsLoadingSessions(true)
    const data = await getSessions()
    setSessions(data)
    if (data.length > 0 && !activeSessionId) {
      setActiveSessionId(data[0].id)
    } else if (data.length === 0) {
      await handleNewChat()
    }
    setIsLoadingSessions(false)
  }

  async function loadMessages(sessionId: string) {
    setIsLoadingMessages(true)
    const data = await getMessages(sessionId)
    setMessages(data)
    setIsLoadingMessages(false)
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadSessions()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!activeSessionId) return
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadMessages(activeSessionId)
  }, [activeSessionId])

  async function handleNewChat() {
    const session = await createSession()
    if (!session) return
    setSessions(prev => [session, ...prev])
    setActiveSessionId(session.id)
    setMessages([])
    setIsLoadingMessages(false)
  }

  function handleSelectSession(sessionId: string) {
    setActiveSessionId(sessionId)
    setMessages([])
  }

  async function handleDeleteSession(sessionId: string) {
    const success = await deleteSession(sessionId)
    if (!success) return
    const remaining = sessions.filter(s => s.id !== sessionId)
    setSessions(remaining)
    if (activeSessionId === sessionId) {
      if (remaining.length > 0) {
        setActiveSessionId(remaining[0].id)
      } else {
        await handleNewChat()
      }
    }
  }

  async function handleRenameSession(sessionId: string, title: string) {
    const updated = await renameSession(sessionId, title)
    if (!updated) {
      toast.error('Failed to rename chat')
      return
    }
    setSessions(prev =>
      prev.map(s => (s.id === sessionId ? { ...s, title } : s)),
    )
  }

  const handleSend = useCallback(async (content: string) => {
    if (!activeSessionId) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      createdAt: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    const aiMessageId = (Date.now() + 1).toString()

    try {
      if (isWeatherMode) {
        const result = await queryDocuments(
          content,
          null,
          activeSessionId,
          { weatherMode: true },
        )
        setMessages(prev => [...prev, {
          id: aiMessageId,
          role: 'assistant',
          content: result.answer,
          sources: result.sources as Source[],
          createdAt: new Date().toISOString(),
        }])
      } else {
        setMessages(prev => [...prev, {
          id: aiMessageId,
          role: 'assistant',
          content: '',
          createdAt: new Date().toISOString(),
        }])
        setStreamingId(aiMessageId)

        await sendMessage(
          content,
          activeSessionId,
          persona,
          (chunk: string) => {
            setMessages(prev => prev.map(msg =>
              msg.id === aiMessageId
                ? { ...msg, content: msg.content + chunk }
                : msg,
            ))
          },
        )
      }

      const updatedSessions = await getSessions()
      setSessions(updatedSessions)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Something went wrong'
      if (!message.includes('quota') && !message.includes('rate')) {
        toast.error('Something went wrong. Please try again.')
      }

      if (isWeatherMode) {
        setMessages(prev => [...prev, {
          id: aiMessageId,
          role: 'assistant',
          content: 'Something went wrong. Please try again.',
          createdAt: new Date().toISOString(),
        }])
      } else {
        setMessages(prev => prev.map(msg =>
          msg.id === aiMessageId
            ? { ...msg, content: 'Something went wrong. Please try again.' }
            : msg,
        ))
      }
    } finally {
      setIsLoading(false)
      setStreamingId(null)
    }
  }, [activeSessionId, isWeatherMode, persona])

  function handleRegenerate() {
    const lastUser = [...messages].reverse().find(m => m.role === 'user')
    if (!lastUser || isLoading) return

    setMessages(prev => {
      const lastAssistantIdx = [...prev].reverse().findIndex(m => m.role === 'assistant')
      if (lastAssistantIdx < 0) return prev
      const cutIdx = prev.length - 1 - lastAssistantIdx
      return prev.slice(0, cutIdx)
    })

    handleSend(lastUser.content)
  }

  const personaSelect = (
    <div className="relative">
      <select
        value={persona}
        onChange={e => setPersona(e.target.value)}
        aria-label="Select AI model persona"
        className="appearance-none text-xs font-medium pl-3 pr-8 py-2 rounded-xl
          bg-[var(--color-surface-raised)] border border-[var(--color-border-subtle)]
          text-[var(--color-text-secondary)] hover:border-violet-500/30
          focus:outline-none focus:ring-2 focus:ring-violet-500/30
          transition-all cursor-pointer"
      >
        {PERSONA_OPTIONS.map(opt => (
          <option key={opt.value} value={opt.value}>
            {opt.emoji} {opt.label}
          </option>
        ))}
      </select>
      <ChevronDown className="w-3.5 h-3.5 absolute right-2.5 top-1/2 -translate-y-1/2
        text-[var(--color-text-muted)] pointer-events-none" aria-hidden />
    </div>
  )

  return (
    <AppShell
      sidebarContent={
        <ChatHistorySidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          loading={isLoadingSessions}
          onNewChat={handleNewChat}
          onSelectSession={handleSelectSession}
          onDeleteSession={handleDeleteSession}
          onRenameSession={handleRenameSession}
        />
      }
      header={
        <PageHeader
          title={activeSession?.title ?? 'AI Chat'}
          subtitle={isWeatherMode ? 'Weather Assistant' : 'Powered by Gemini'}
          icon={<MessageSquare className="w-4 h-4 text-violet-500" />}
          actions={personaSelect}
          user={user}
        />
      }
    >
      {isWeatherMode && (
        <WeatherQuickChips onSelect={handleSend} disabled={isLoading} />
      )}

      <ChatWindow
        messages={messages}
        isLoading={isLoading}
        isLoadingMessages={isLoadingMessages && messages.length === 0}
        loadingMessage={isWeatherMode && isLoading ? WEATHER_LOADING_MESSAGE : undefined}
        suggestedPrompts={!isWeatherMode ? AI_SUGGESTED_PROMPTS : undefined}
        onSuggestedPrompt={handleSend}
        streamingMessageId={streamingId}
        onRegenerate={handleRegenerate}
      />

      <MessageInput
        onSend={handleSend}
        isLoading={isLoading}
        placeholder={
          isWeatherMode
            ? 'Ask about the weather in any city...'
            : 'Ask me anything...'
        }
      />
    </AppShell>
  )
}
