'use client'
import { useState, useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useTheme } from '@/components/ThemeProvider'
import toast from 'react-hot-toast'
import {
  sendMessage,
  getMessages,
  getSessions,
  createSession,
  deleteSession
} from '@/lib/api'
import { logout } from '@/lib/auth'
import ChatWindow from '@/components/chat/ChatWindow'
import MessageInput from '@/components/chat/MessageInput'
import SessionSidebar from '@/components/chat/SessionSidebar'
import type { Message, ChatSession } from '@/types'

export default function ChatPage() {
  const { user, loading } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [activeSessionId, setActiveSessionId] = useState<string>('')

  // Load sessions on mount
  useEffect(() => {
    if (!user) return
    loadSessions()
  }, [user])

  // Load messages when session changes
  useEffect(() => {
    if (!activeSessionId) return
    loadMessages(activeSessionId)
  }, [activeSessionId])

  async function loadSessions() {
    const data = await getSessions()
    setSessions(data)
    if (data.length > 0) {
      setActiveSessionId(data[0].id)
    } else {
      // Create first session automatically
      handleNewChat()
    }
  }

  async function loadMessages(sessionId: string) {
    const data = await getMessages(sessionId)
    setMessages(data)
  }

  async function handleNewChat() {
    const session = await createSession()
    if (!session) {
      toast.error('Failed to create new chat')
      return
    }
    setSessions(prev => [session, ...prev])
    setActiveSessionId(session.id)
    setMessages([])
    toast.success('New chat started!')
  }

  async function handleSelectSession(sessionId: string) {
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
        handleNewChat()
      }
    }
  }

  async function handleSend(content: string) {
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
    setMessages(prev => [...prev, {
      id: aiMessageId,
      role: 'assistant',
      content: '',
      createdAt: new Date().toISOString(),
    }])

    try {
      await sendMessage(content, activeSessionId, (chunk: string) => {
        setMessages(prev => prev.map(msg =>
          msg.id === aiMessageId
            ? { ...msg, content: msg.content + chunk }
            : msg
        ))
      })

      // Refresh sessions to update title
      const updatedSessions = await getSessions()
      setSessions(updatedSessions)

    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      // Only show generic error if not already shown by api.ts
      if (!message.includes('quota') && !message.includes('rate') && !message.includes('429')) {
        toast.error('Something went wrong. Please try again.')
      }
      setMessages(prev => prev.map(msg =>
        msg.id === aiMessageId
          ? { ...msg, content: 'Something went wrong. Please try again.' }
          : msg
      ))
    } finally {
      setIsLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center
        justify-center bg-gray-50 dark:bg-gray-950">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-indigo-600
            border-t-transparent rounded-full animate-spin"/>
          <p className="text-sm text-gray-400">Loading...</p>
        </div>
      </div>
    )
  }

  const activeSession = sessions.find(s => s.id === activeSessionId)

  return (
    <div className="flex h-screen bg-white dark:bg-gray-900
      overflow-hidden">

      {/* Sidebar */}
      <SessionSidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
        username={user?.username ?? ''}
        onLogout={logout}
      />

      {/* Main chat area */}
      <main className="flex-1 flex flex-col min-w-0">

        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100
          dark:border-gray-700 bg-white dark:bg-gray-900
          flex items-center justify-between">
          <div>
            <h1 className="text-sm font-medium text-gray-700
              dark:text-gray-200">
              {activeSession?.title ?? 'New Conversation'}
            </h1>
            <p className="text-xs text-gray-400 dark:text-gray-500">
              Powered by AI
            </p>
          </div>
          <button
            onClick={toggleTheme}
            className="text-gray-500 dark:text-gray-400
            hover:text-gray-700 dark:hover:text-gray-200
            transition-colors p-2 rounded-lg
            hover:bg-gray-100 dark:hover:bg-gray-800"
            title="Toggle dark mode"
          >
            {theme === 'light' ? (
              <svg xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24" fill="currentColor"
                className="w-5 h-5">
                <path fillRule="evenodd" d="M9.528 1.718a.75.75 0 01.162.819A8.97 8.97 0 009 6a9 9 0 009 9 8.97 8.97 0 003.463-.69.75.75 0 01.981.98 10.503 10.503 0 01-9.694 6.46c-5.799 0-10.5-4.701-10.5-10.5 0-4.368 2.667-8.112 6.46-9.694a.75.75 0 01.818.162z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24" fill="currentColor"
                className="w-5 h-5">
                <path d="M12 2.25a.75.75 0 01.75.75v2.25a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM7.5 12a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM18.894 6.166a.75.75 0 00-1.06-1.06l-1.591 1.59a.75.75 0 101.06 1.061l1.591-1.59zM21.75 12a.75.75 0 01-.75.75h-2.25a.75.75 0 010-1.5H21a.75.75 0 01.75.75zM17.834 18.894a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 10-1.061 1.06l1.59 1.591zM12 18a.75.75 0 01.75.75V21a.75.75 0 01-1.5 0v-2.25A.75.75 0 0112 18zM7.758 17.303a.75.75 0 00-1.061-1.06l-1.591 1.59a.75.75 0 001.06 1.061l1.591-1.59zM6 12a.75.75 0 01-.75.75H3a.75.75 0 010-1.5h2.25A.75.75 0 016 12zM6.697 7.757a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 00-1.061 1.06l1.59 1.591z" />
              </svg>
            )}
          </button>
        </div>

        {/* Chat */}
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
        />

        {/* Input */}
        <MessageInput
          onSend={handleSend}
          isLoading={isLoading}
        />
      </main>
    </div>
  )
}